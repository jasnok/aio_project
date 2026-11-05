"""8012 포트에서 독립 실행되는 날씨 Streamable HTTP MCP Server입니다."""

import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Literal
from rag_common import search_similar_chunks
import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


load_dotenv(Path(__file__).resolve().parents[1] / ".env")  # 다른 os.getenv보다 반드시 먼저!

MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("WEATHER_MCP_PORT", "8012"))
KMA_API_KEY = os.getenv("WEATHER_API_KEY")

mcp = FastMCP(
    "mini-agent-weather",
    instructions="도시의 현재 날씨와 예보를 기상청 API로 제공하는 교육용 서버입니다.",
    host=MCP_HOST,
    port=MCP_PORT,
    stateless_http=True,
    json_response=True,
)

# ── 현재 날씨: 기상청 API 허브 지상관측(ASOS) ────────────────────────────
KMA_ASOS_URL = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"

# ASOS 관측지점번호. 필요한 도시는 여기에 계속 추가하면 됩니다.
STATION_BY_CITY = {
    "서울": "108", "부산": "159", "인천": "112", "대구": "143",
    "대전": "133", "광주": "156", "울산": "152", "수원": "119",
    "강릉": "105", "전주": "146", "청주": "131", "창원": "155",
    "제주": "184",
}

# kma_sfctm2 응답 컬럼 순서 (기상청 API 허브 문서 기준). help=1로 한 번
# 직접 호출해서 실제 헤더와 일치하는지 반드시 확인하세요.
_ASOS_COLUMNS = [
    "TM", "STN", "WD", "WS", "GST_WD", "GST_WS", "GST_TM", "PA", "PS",
    "PT", "PR", "TA", "TD", "HM", "PV", "RN", "RN_DAY", "RN_JUN",
    "RN_INT", "SD_HR3", "SD_DAY", "SD_TOT", "WC", "WP", "WW", "CA",
    "CA_TOT", "CH", "CT", "CT_TOP", "CT_MID", "CT_LOW", "VS", "SS",
    "SI", "ST", "TS", "TE", "TE_005", "TE_01", "TE_02", "TE_03",
    "ST_GD", "WH", "BF", "IR", "IX",
]


def _require_supported_city(city: str, catalog: dict) -> str:
    normalized = city.strip()
    if normalized not in catalog:
        supported = ", ".join(sorted(catalog))
        raise ValueError(f"지원하지 않는 도시입니다: {city} (지원 도시: {supported})")
    return normalized

async def _fetch_asos_record(client: httpx.AsyncClient, stn: str) -> dict:
    now = datetime.now()
    for hours_back in range(1, 4):  # 1시간 전 → 2시간 전 → 3시간 전 순으로 시도
        tm = (now - timedelta(hours=hours_back)).strftime("%Y%m%d%H00")
        response = await client.get(KMA_ASOS_URL, params={
            "tm": tm, "stn": stn, "help": 0, "authKey": KMA_API_KEY,
        })
        response.raise_for_status()
        data_lines = [
            line for line in response.text.splitlines()
            if line.strip() and not line.startswith("#")
        ]
        if data_lines:
            return dict(zip(_ASOS_COLUMNS, data_lines[-1].split()))
    raise ValueError("최근 3시간 내 관측 데이터를 찾을 수 없습니다.")


@mcp.tool()
async def get_current_weather(city: str) -> dict:
    """도시의 현재 날씨를 기상청 ASOS 관측 API로 조회합니다."""
    normalized = _require_supported_city(city, STATION_BY_CITY)
    stn = STATION_BY_CITY[normalized]

    async with httpx.AsyncClient(timeout=10) as client:
        record = await _fetch_asos_record(client, stn)

    return {
        "city": normalized,
        "condition": None,
        "temperature_c": float(record["TA"]),
        "humidity_percent": float(record["HM"]),
        "source": "kma-asos-api",
    }


# ── 예보: 기상청 단기예보(동네예보) ──────────────────────────────────────
# TODO: 아래 URL은 본인 API 허브 "활용신청 내역"에서 발급받은 정확한
# 단기예보 조회서비스(getVilageFcst) 주소로 확인 후 바꿔주세요.
KMA_FORECAST_URL = "https://apihub.kma.go.kr/api/typ02/openApi/VilageFcstInfoService_2.0/getVilageFcst"

# 기상청 동네예보 격자좌표(nx, ny). 도시를 늘리려면 여기에 추가합니다.
GRID_BY_CITY = {
    "서울": (60, 127), "부산": (98, 76), "인천": (55, 124), "대구": (89, 90),
    "대전": (67, 100), "광주": (58, 74), "울산": (102, 84), "수원": (60, 121),
    "강릉": (92, 131), "전주": (63, 89), "청주": (69, 106), "창원": (90, 77),
    "제주": (52, 38),
}

_SKY_TEXT = {"1": "맑음", "3": "구름 많음", "4": "흐림"}
_PTY_TEXT = {"0": "", "1": "비", "2": "비/눈", "3": "눈", "4": "소나기"}
_BASE_HOURS = ["02", "05", "08", "11", "14", "17", "20", "23"]


def _latest_base_datetime(now: datetime) -> tuple[str, str]:
    """가장 최근에 발표된 단기예보 시각(base_date, base_time)을 계산합니다."""
    candidate = now - timedelta(minutes=10)  # 발표 후 배포 지연 여유
    for hour in reversed(_BASE_HOURS):
        base_dt = candidate.replace(hour=int(hour), minute=0, second=0, microsecond=0)
        if base_dt <= candidate:
            return base_dt.strftime("%Y%m%d"), f"{hour}00"
    # 새벽 02시 이전이면 전날 23시 발표분을 씁니다.
    yesterday = candidate - timedelta(days=1)
    return yesterday.strftime("%Y%m%d"), "2300"


@mcp.tool()
async def get_weather_forecast(city: str, days: int = 3) -> dict:
    """도시의 향후 날씨 예보를 기상청 단기예보 API로 조회합니다. days는 최대 3일입니다."""
    normalized = _require_supported_city(city, GRID_BY_CITY)
    if days < 1 or days > 3:
        raise ValueError("days는 1~3 사이여야 합니다.")

    nx, ny = GRID_BY_CITY[normalized]
    base_date, base_time = _latest_base_datetime(datetime.now())

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(KMA_FORECAST_URL, params={
            "serviceKey": KMA_API_KEY,
            "pageNo": 1,
            "numOfRows": 1000,
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
        })
        response.raise_for_status()
        body = response.json()

    items = body["response"]["body"]["items"]["item"]

    by_date: dict[str, dict] = {}
    for item in items:
        entry = by_date.setdefault(item["fcstDate"], {})
        category = item["category"]
        if category == "TMN":
            entry["temp_min_c"] = float(item["fcstValue"])
        elif category == "TMX":
            entry["temp_max_c"] = float(item["fcstValue"])
        elif category == "SKY":
            entry["sky_code"] = item["fcstValue"]
        elif category == "PTY":
            entry["pty_code"] = item["fcstValue"]

    today = date.today()
    forecast = []
    for offset in range(1, days + 1):
        target = (today + timedelta(days=offset)).strftime("%Y%m%d")
        entry = by_date.get(target)
        if entry is None:
            continue
        precipitation = _PTY_TEXT.get(entry.get("pty_code", "0"), "")
        condition = precipitation or _SKY_TEXT.get(entry.get("sky_code"), "정보 없음")
        forecast.append({
            "date": target,
            "condition": condition,
            "temp_min_c": entry.get("temp_min_c"),
            "temp_max_c": entry.get("temp_max_c"),
        })

    return {
        "city": normalized,
        "forecast": forecast,
        "source": "kma-vilagefcst-api",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")