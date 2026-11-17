"""한국관광공사 TourAPI 호출과 지역코드 캐시를 담당합니다."""

from typing import Any
from urllib.parse import unquote

import httpx

from config import TourSpotSettings
from constants.tour_api import API_ERROR_MESSAGES, TOURIST_ATTRACTION_CONTENT_TYPE
from exceptions import TourApiError
from mappers import extract_items
from schemas.location import Region, ResolvedLocation


class TourApiRepository:
    def __init__(
        self,
        settings: TourSpotSettings,
        client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings
        self.client = client
        self._district_cache: dict[str, list[Region]] = {}

    def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.service_key:
            raise TourApiError(
                "TOUR_API_SERVICE_KEY가 없습니다. .env에 API 인증키를 입력해 주세요."
            )

        common_params = {
            "serviceKey": unquote(self.settings.service_key),
            "MobileOS": "ETC",
            "MobileApp": "mini-agent-tour-spot",
            "_type": "json",
        }
        request_params = {**common_params, **params}
        url = f"{self.settings.api_base_url}/{endpoint}"

        try:
            if self.client is not None:
                response = self.client.get(url, params=request_params)
            else:
                response = httpx.get(
                    url,
                    params=request_params,
                    timeout=self.settings.api_timeout,
                )
            response.raise_for_status()
        except httpx.TimeoutException as error:
            raise TourApiError("공공데이터 API 응답 시간이 초과됐습니다.") from error
        except httpx.HTTPError as error:
            raise TourApiError(f"공공데이터 API 연결에 실패했습니다: {error}") from error

        try:
            payload = response.json()
        except ValueError as error:
            raise TourApiError(
                "공공데이터 API가 JSON이 아닌 응답을 반환했습니다. "
                "API 키와 주소를 확인해 주세요."
            ) from error

        response_payload = payload.get("response")
        if not isinstance(response_payload, dict):
            raise TourApiError("공공데이터 API 응답 형식을 확인할 수 없습니다.")

        header = response_payload.get("header", {})
        result_code = str(header.get("resultCode", ""))
        if result_code != "0000":
            result_message = str(header.get("resultMsg", "알 수 없는 오류"))
            friendly = API_ERROR_MESSAGES.get(
                result_code,
                "공공데이터 API 요청에 실패했습니다.",
            )
            raise TourApiError(f"{friendly} ({result_code}: {result_message})")

        body = response_payload.get("body", {})
        if not isinstance(body, dict):
            raise TourApiError("공공데이터 API의 body 형식이 올바르지 않습니다.")
        return body

    def get_districts(self, area_code: str) -> list[Region]:
        """광역시도에 속한 시군구를 조회하고 프로세스 안에서 캐시합니다."""
        cached = self._district_cache.get(area_code)
        if cached is not None:
            return cached

        body = self._request(
            "areaCode2",
            {"areaCode": area_code, "numOfRows": 100, "pageNo": 1},
        )
        districts = [
            Region(str(item.get("code", "")), str(item.get("name", "")))
            for item in extract_items(body)
            if item.get("code") and item.get("name")
        ]
        self._district_cache[area_code] = districts
        return districts

    def search_attractions(
        self,
        resolved: ResolvedLocation,
        limit: int,
    ) -> dict[str, Any]:
        """확정된 지역코드로 관광지 목록 원본 응답을 조회합니다."""
        params: dict[str, Any] = {
            "contentTypeId": TOURIST_ATTRACTION_CONTENT_TYPE,
            "numOfRows": limit,
            "pageNo": 1,
        }
        if resolved.area_code:
            params["areaCode"] = resolved.area_code
        if resolved.sigungu_code:
            params["sigunguCode"] = resolved.sigungu_code
        return self._request("areaBasedList2", params)
