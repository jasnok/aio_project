"""키 없이 자동 등록 화면을 설명하기 위한 고정된 가상 분석 결과."""

from copy import deepcopy


SAMPLE_ANALYSIS = [
    {
        "title": "[포트폴리오 시연용 가상 공고] 금천 청년 임대",
        "housing_name": "가상 금천 청년주택 26㎡형",
        "area_sqm": "26.5",
        "recruitment_count": "12",
        "location": "금천구",
        "detail_address": "",
        "deposit": "10000000",
        "monthly_rent": None,
        "application_start_date": "2026-10-01",
        "application_end_date": "2026-10-31",
        "description": "포트폴리오 시연을 위해 만든 가상 공고입니다. 실제 모집 정보가 아닙니다.",
        "source_url": "https://example.invalid/portfolio-demo/v1/auto-sample",
    }
]


def sample_analysis() -> list[dict]:
    """화면에서 수정해도 원본 샘플이 바뀌지 않도록 복사합니다."""

    return deepcopy(SAMPLE_ANALYSIS)
