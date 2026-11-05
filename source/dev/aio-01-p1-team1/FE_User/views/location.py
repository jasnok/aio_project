"""등록된 청약 공고를 검색하고 주변 생활권을 지도에 표시하는 화면입니다."""

from core.location_search import listing_label
from core.session_result import session_result

import streamlit as st
from clients.listing_client import search_location_listings
from clients.location_client import (
    geocode_location,
    get_nearby_facilities,
)
from core.api_client import BackendAPIError
from core.location_map import build_location_deck
from core.ui import page_header
from core.listing_view import (
    address_line,
    description_lines,
    format_description_line,
    format_won,
    period_line,
    summary_line,
)

DEFAULT_RADIUS_M = 2000
DEFAULT_FACILITY_LIMIT = 3

RADIUS_OPTIONS = {
    "1km": 1000,
    "2km": 2000,
    "3km": 3000,
}


def load_analysis(address, radius):
    location = geocode_location(address).get("data") or {}
    if location.get("latitude") is None or location.get("longitude") is None:
        raise BackendAPIError("공고 주소의 좌표를 확인할 수 없습니다.")
    facilities = get_nearby_facilities(
        latitude=location["latitude"], longitude=location["longitude"],
        radius_m=radius, limit=DEFAULT_FACILITY_LIMIT,
    ).get("data") or {}
    return location, facilities


@st.dialog("공고 상세정보", width="large")
def show_listing_detail(listing: dict) -> None:
    """선택한 청약 공고의 상세정보를 팝업으로 표시합니다."""

    housing_name = str(
        listing.get("housing_name") or "주택명 없음"
    )
    title = str(
        listing.get("title") or "공고명 없음"
    )

    st.subheader(housing_name)
    st.caption(title)

    summary = summary_line(listing)
    if summary:
        st.write(summary)

    address = address_line(listing)
    if address:
        st.write(address)

    deposit_column, rent_column = st.columns(2)

    with deposit_column:
        st.caption("보증금")
        st.markdown(
            f"**{format_won(listing.get('deposit'))}**"
        )

    with rent_column:
        st.caption("월 임대료")
        st.markdown(
            f"**{format_won(listing.get('monthly_rent'))}**"
        )

    st.caption(period_line(listing))

    description = description_lines(listing)
    if description:
        st.divider()
        st.markdown("#### 상세 내용")

        for line in description:
            st.markdown(format_description_line(line))

    source_url = listing.get("source_url")
    if source_url:
        st.link_button(
            "공고 원문 보기",
            source_url,
            use_container_width=True,
        )



def render() -> None:
    page_header(
        "🚇",
        "주변생활권 분석",
        "청약정보에 등록된 공고명 또는 공고주소를 검색하면 "
        "주변 지하철역·마트·병원 정보를 알려드립니다.",
    )


    with st.form("location-search-form"):
        query = st.text_input(
            "공고명 또는 공고주소",
            placeholder="예: 행복주택 입주자 모집공고",
        )

        selected_radius = st.selectbox(
            "생활권 검색 반경",
            options=list(RADIUS_OPTIONS),
            index=1,
        )

        submitted = st.form_submit_button(
            "주변생활권 탐색",
            type="primary",
            use_container_width=True,
        )


    if submitted:
        query = query.strip()

        if not query:
            st.warning("공고명 또는 공고주소를 입력해 주세요.")
            st.stop()

        try:
            with st.spinner("청약정보에서 공고를 검색하는 중입니다..."):
                listing_response = search_location_listings(query)
                page = listing_response.get("data") or {}
                matching_listings = page.get("items") or []
        except BackendAPIError as error:
            st.error(str(error))
            st.stop()

        st.session_state["location-query"] = query
        st.session_state["location-page"] = page
        st.session_state.pop("location-analysis-cache", None)
        if not matching_listings:
            st.session_state.pop("location-search-matches", None)
            st.error(
                "청약정보 내에서 일치하는 공고를 찾을 수 없습니다. "
                "공고명 또는 공고주소를 다시 확인해 주세요."
            )
            st.stop()

        st.session_state["location-search-matches"] = matching_listings
        st.session_state["location-search-radius"] = RADIUS_OPTIONS.get(
            selected_radius,
            DEFAULT_RADIUS_M,
        )
        st.session_state["location-search-radius-label"] = selected_radius


    page = st.session_state.get("location-page", {})
    if page.get("total_pages", 1) > 1:
        st.caption(f"공고 후보 {page['total_count']}건 · {page['page']} / {page['total_pages']} 페이지")
        previous, following = st.columns(2)
        back = previous.button("이전 후보", disabled=page['page'] <= 1)
        forward = following.button("다음 후보", disabled=page['page'] >= page['total_pages'])
        if back or forward:
            try:
                response = search_location_listings(st.session_state["location-query"], page['page'] + (1 if forward else -1))
                st.session_state["location-page"] = response['data']
                st.session_state["location-search-matches"] = response['data']['items']
                st.rerun()
            except BackendAPIError as error:
                st.error(str(error))

    matching_listings = st.session_state.get(
        "location-search-matches",
        [],
    )

    if matching_listings:
        selected_listing = st.selectbox(
            "분석할 공고 선택",
            options=matching_listings,
            format_func=listing_label,
        )

        listing_address = str(
            selected_listing.get("detail_address") or ""
        ).strip()

        if not listing_address:
            st.error(
                "선택한 공고에 상세주소가 등록되어 있지 않아 "
                "생활권을 분석할 수 없습니다."
            )
            st.stop()

        radius_m = st.session_state.get(
            "location-search-radius",
            DEFAULT_RADIUS_M,
        )

        try:
            with st.spinner("공고 주소와 주변 생활권을 검색하는 중입니다..."):
                if st.button("생활권 결과 새로고침"):
                    st.session_state.pop("location-analysis-cache", None)
                location, facilities = session_result(
                    st.session_state, "location-analysis-cache",
                    (selected_listing.get("id"), listing_address, radius_m, DEFAULT_FACILITY_LIMIT),
                    lambda: load_analysis(listing_address, radius_m), ttl=300,
                )
                latitude, longitude = location["latitude"], location["longitude"]
                stations, marts, hospitals = (facilities.get(name) or [] for name in ("subways", "marts", "hospitals"))
        except BackendAPIError as error:
            st.error(str(error))
            st.stop()

        listing_title = str(
            selected_listing.get("title") or "공고명 없음"
        )

        st.subheader("선택한 공고")

        if st.button(
            listing_title,
            key=f"location-listing-detail-{selected_listing.get('id')}",
        ):
            show_listing_detail(selected_listing)

        st.caption(location.get("address") or listing_address)

        st.subheader("주변 생활권 지도")

        location_deck = build_location_deck(
            title=listing_title,
            latitude=float(latitude),
            longitude=float(longitude),
            stations=stations,
            marts=marts,
            hospitals=hospitals,
            radius_m=radius_m,
        )

        st.pydeck_chart(
            location_deck,
            use_container_width=True,
        )

        st.caption(
            "🏠 공고 위치 · 🚇 지하철역 · "
            "🛒 마트 · 🏥 병원"
        )
