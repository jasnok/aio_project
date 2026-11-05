"""기상청 단기예보 API 클라이언트입니다."""

import logging
from datetime import datetime

import httpx

from ..core.config import settings
from ..core.errors import WeatherProviderError


logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def request_forecast(endpoint: str, base_time: datetime, nx: int, ny: int) -> list:
    if not settings.kma_api_key:
        raise WeatherProviderError("KMA_API_KEY가 없습니다. .env 파일을 확인해 주세요.")
    params = {
        "serviceKey": settings.kma_api_key,
        "pageNo": 1,
        "numOfRows": 1000,
        "dataType": "JSON",
        "base_date": base_time.strftime("%Y%m%d"),
        "base_time": base_time.strftime("%H%M"),
        "nx": nx,
        "ny": ny,
    }
    try:
        response = httpx.get(
            f"{settings.kma_api_base_url}/{endpoint}",
            params=params,
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.RequestError:
        raise WeatherProviderError("기상청 API 네트워크 연결에 실패했습니다.") from None
    except httpx.HTTPStatusError as error:
        raise WeatherProviderError(
            "기상청 API HTTP 오류: "
            f"{error.response.status_code} (설정 버전: {settings.kma_api_version})"
        ) from None
    except ValueError:
        raise WeatherProviderError(
            "기상청 API가 JSON 형식으로 응답하지 않았습니다. "
            f"KMA_API_VERSION={settings.kma_api_version} 설정을 확인해 주세요."
        ) from None
    header = data.get("response", {}).get("header", {})
    result_code = str(header.get("resultCode", ""))
    if result_code not in {"0", "00"}:
        result_message = header.get("resultMsg", "알 수 없는 오류")
        raise WeatherProviderError(
            f"기상청 API 오류: {result_code} {result_message}"
        )
    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    if not items:
        raise WeatherProviderError("기상청 API 응답에 날씨 데이터가 없습니다.")
    return items
