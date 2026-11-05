"""Network-free candidate services used by the explicit mock provider."""

from uuid import UUID

from app.landmark_schemas import LandmarkCandidate, LandmarkSearchResult
from app.places.models import GuidePlace, SearchIntent, SearchResponse


class MockLandmarkSearchService:
    async def search(self, *, destination, queries, limit):
        items = [
            LandmarkCandidate(
                id="mock-landmark-1", name="해운대해수욕장",
                category_name="여행 > 관광명소 > 해수욕장",
                address="부산 해운대구 우동", road_address="부산 해운대구 해운대해변로 264",
                latitude=35.1587, longitude=129.1604, phone="",
                kakao_place_url="https://place.map.kakao.com/mock-landmark-1",
            ),
            LandmarkCandidate(
                id="mock-landmark-2", name="광안리해수욕장",
                category_name="여행 > 관광명소 > 해수욕장",
                address="부산 수영구 광안동", road_address="부산 수영구 광안해변로 219",
                latitude=35.1532, longitude=129.1186, phone="",
                kakao_place_url="https://place.map.kakao.com/mock-landmark-2",
            ),
        ]
        return LandmarkSearchResult(landmarks=items[:limit])


class MockPlaceSearchService:
    async def search(self, request):
        specs = [
            (101, "mock-food-1", "부산 해산물 식당", "해물,생선", 35.1587, 129.1604),
            (102, "mock-food-2", "부산 돼지국밥", "한식", 35.1013, 129.0301),
            (103, "mock-food-3", "광안리 밀면", "한식", 35.1531, 129.1186),
            (104, "mock-food-4", "자갈치 시장 회센터", "해물,생선", 35.0969, 129.0302),
        ]
        items = [
            GuidePlace(
                id=UUID(int=number), kakao_place_id=kakao_id, name=name,
                category_name=f"음식점 > {category}", category_group_code="FD6",
                address="부산광역시", road_address="부산광역시 테스트로 1",
                latitude=latitude, longitude=longitude,
                kakao_place_url=f"https://place.map.kakao.com/{kakao_id}",
            )
            for number, kakao_id, name, category, latitude, longitude in specs
        ]
        return SearchResponse(
            intent=SearchIntent(
                district=request.district, category=request.category,
                keyword=request.keyword, query="부산 mock 음식점",
            ),
            places=items[:request.limit],
        )
