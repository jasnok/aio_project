"""호텔 정책 RAG MCP Tool입니다."""

from ..schemas import SearchHotelPoliciesInput, SearchHotelPoliciesOutput
from ..services import policy_service


def search_hotel_policies(
    hotel_ids: list[str], question: str, top_k_per_hotel: int = 2
) -> dict:
    """검색된 호텔 ID들의 정책에서 취소·환불 등 질문과 관련된 규정을 찾습니다."""
    result = policy_service.search(SearchHotelPoliciesInput(
        hotel_ids=hotel_ids,
        question=question,
        top_k_per_hotel=top_k_per_hotel,
    ))
    return SearchHotelPoliciesOutput.model_validate(result).model_dump(mode="json")
