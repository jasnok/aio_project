"""기상청 응답을 현재 날씨 결과로 변환합니다."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ..external_clients import request_forecast
from ..schemas import WeatherLocationInput


KST = ZoneInfo("Asia/Seoul")
REGIONS = {
    "서울": {"nx": 60, "ny": 127}, "부산": {"nx": 98, "ny": 76},
    "인천": {"nx": 55, "ny": 124}, "대전": {"nx": 67, "ny": 100},
    "대구": {"nx": 89, "ny": 90}, "광주": {"nx": 58, "ny": 74},
    "울산": {"nx": 102, "ny": 84}, "세종": {"nx": 66, "ny": 103},
}
SKY_CODES = {"1": "맑음", "3": "구름많음", "4": "흐림"}
PTY_CODES = {
    "0": "강수 없음", "1": "비", "2": "비/눈", "3": "눈",
    "4": "소나기", "5": "빗방울", "6": "빗방울/눈날림", "7": "눈날림",
}


def latest_observation_time(now: datetime) -> datetime:
    if now.minute < 10:
        now -= timedelta(hours=1)
    return now.replace(minute=0, second=0, microsecond=0)


def latest_forecast_time(now: datetime) -> datetime:
    if now.minute < 45:
        now -= timedelta(hours=1)
    return now.replace(minute=30, second=0, microsecond=0)


def nearest_sky(items: list, now: datetime) -> tuple[str, str]:
    sky_items = []
    for item in items:
        if item.get("category") == "SKY":
            forecast_time = datetime.strptime(
                item["fcstDate"] + item["fcstTime"], "%Y%m%d%H%M"
            ).replace(tzinfo=KST)
            sky_items.append((forecast_time, str(item["fcstValue"])))
    if not sky_items:
        raise RuntimeError("초단기예보 응답에 SKY 데이터가 없습니다.")
    forecast_time, sky_code = min(sky_items, key=lambda value: abs(value[0] - now))
    return (
        SKY_CODES.get(sky_code, f"알 수 없는 하늘상태({sky_code})"),
        forecast_time.strftime("%Y-%m-%d %H:%M"),
    )


def current_weather(request: WeatherLocationInput, now: datetime | None = None) -> dict:
    if request.location not in REGIONS:
        raise ValueError(
            f"지원하지 않는 지역입니다: {request.location}. "
            f"지원 지역: {', '.join(REGIONS)}"
        )
    current_time = now or datetime.now(KST)
    region = REGIONS[request.location]
    observation_time = latest_observation_time(current_time)
    forecast_time = latest_forecast_time(current_time)
    observation_items = request_forecast(
        "getUltraSrtNcst", observation_time, region["nx"], region["ny"]
    )
    forecast_items = request_forecast(
        "getUltraSrtFcst", forecast_time, region["nx"], region["ny"]
    )
    observations = {item["category"]: item["obsrValue"] for item in observation_items}
    sky, sky_forecast_at = nearest_sky(forecast_items, current_time)
    precipitation_type = PTY_CODES.get(str(observations.get("PTY", "")), "알 수 없음")
    weather = precipitation_type if precipitation_type != "강수 없음" else sky
    return {
        "location": request.location,
        "observed_at": observation_time.strftime("%Y-%m-%d %H:%M"),
        "sky_forecast_at": sky_forecast_at,
        "temperature_c": observations.get("T1H"),
        "humidity_percent": observations.get("REH"),
        "precipitation_1h_mm": observations.get("RN1"),
        "precipitation_type": precipitation_type,
        "sky": sky, "weather": weather,
        "wind_speed_mps": observations.get("WSD"),
        "data_note": "기온·습도·강수·바람은 실황, 하늘상태는 가장 가까운 초단기예보입니다.",
        "source": "기상청 단기예보 조회서비스",
    }


def next_week_weather(request: WeatherLocationInput) -> dict:
    return {
        "location": request.location,
        "message": "다음 주 날씨 Tool 연결에 성공했습니다.",
        "status": "temporary",
    }
