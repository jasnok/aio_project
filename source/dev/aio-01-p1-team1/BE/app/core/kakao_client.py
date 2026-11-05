# app/core/kakao_client.py
# 카카오 키 로딩, 카카오 API 호출

import httpx
from housing_config import ConfigurationError
from app.core.settings import settings

KAKAO_ADDRESS_SEARCH_URL = (
    "https://dapi.kakao.com/v2/local/search/address.json"
)
KAKAO_REQUEST_TIMEOUT = 5.0


class KakaoGeocodingError(Exception):
    pass


def get_kakao_rest_api_key() -> str:
    try:
        return settings.require("KAKAO_REST_API_KEY")
    except ConfigurationError as error:
        raise KakaoGeocodingError(str(error)) from error


def address_to_coordinates(
    address: str,
    rest_api_key: str,
) -> tuple[float, float] | None:
    # 현재 favorite_service.py의 함수 내용을 그대로 이동
    ...
