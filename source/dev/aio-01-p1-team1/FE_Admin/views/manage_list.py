"""관리자 공고 관리 화면의 역할별 구성 요소."""


import streamlit as st

from clients.listing_client import delete_listing, get_listings_page, search_listings
from core.constants import SEOUL_DISTRICTS
from core.bulk_delete import can_delete, checkbox_key, picked_ids, set_all
from core.image_gallery import count_label, image_list, rows_of
from core.listing_view import (
    address_line,
    card_title,
    description_preview,
    description_lines,
    format_description_line,
    format_won,
    period_line,
    summary_line,
)
from core.listing_sort import (
    DEFAULT_LABEL,
    default_index,
    sort_key,
    sort_labels,
)
from core.page_params import build_params


# 이미지 크기 제한입니다. 백엔드에서도 같은 값으로 다시 검사합니다.
MAX_IMAGE_SIZE = 5 * 1024 * 1024

# 한 페이지에 보여줄 공고 수입니다.
PAGE_SIZE = 10

# 고른 정렬 기준을 담아 둘 자리입니다.
SORT_STATE_KEY = "admin-listing-sort"



class ListingListView:
    def show_listing_list(self) -> None:
        """공고 목록과 검색, 수정/삭제 버튼을 보여줍니다."""

        # 입력칸의 처음 값은 주소창에 담긴 검색 조건을 따릅니다.
        # 그래야 수정 화면에 다녀오거나 새로고침해도 조건이 그대로 보입니다.
        district_options = ("전체",) + SEOUL_DISTRICTS
        saved_location = self.current_search.get("location", "전체")
        location_index = (
            district_options.index(saved_location) if saved_location in district_options else 0
        )

        with st.expander("조건검색", expanded=bool(self.current_search)):
            with st.form("listing_search_form"):
                search_location = st.selectbox("자치구", district_options, index=location_index)
                search_max_deposit = st.number_input(
                    "최대 보증금",
                    min_value=0,
                    step=10000,
                    value=int(self.current_search.get("max_deposit", 0)),
                )
                search_max_monthly_rent = st.number_input(
                    "최대 월세",
                    min_value=0,
                    step=10000,
                    value=int(self.current_search.get("max_monthly_rent", 0)),
                )
                st.selectbox(
                    "정렬 기준",
                    sort_labels(),
                    index=default_index(),
                    key=SORT_STATE_KEY,
                    help="검색을 누르면 고른 순서로 다시 정렬합니다.",
                )
                search_submitted = st.form_submit_button("검색")

        # 고른 정렬 기준은 st.session_state에 남습니다.
        # 페이지를 넘기거나 수정 화면에 다녀와도 순서가 유지됩니다.
        current_sort_label = st.session_state.get(SORT_STATE_KEY, DEFAULT_LABEL)
        current_sort = sort_key(current_sort_label)

        if search_submitted:
            # 검색 조건을 주소창에 적어 두고 다시 그립니다.
            # 조건을 화면 변수에만 두면 수정 화면에 다녀왔을 때 사라집니다.
            new_search = {}
            if search_location != "전체":
                new_search["location"] = search_location
            if int(search_max_deposit) > 0:
                new_search["max_deposit"] = str(int(search_max_deposit))
            if int(search_max_monthly_rent) > 0:
                new_search["max_monthly_rent"] = str(int(search_max_monthly_rent))
            # 조건이 그대로면 주소를 다시 쓰지 않습니다.
            # 같은 값을 써도 방문 기록이 쌓여 뒤로가기가 헛돌기 때문입니다.
            target_params = build_params(1, None, new_search)
            if st.query_params.to_dict() != target_params:
                st.query_params.from_dict(target_params)
                st.rerun()

        if self.current_search:
            params = {"location": self.current_search["location"]} if "location" in self.current_search else {}
            for name in ("max_deposit", "max_monthly_rent"):
                if name in self.current_search:
                    params[name] = int(self.current_search[name])
            params["sort"] = current_sort
            with st.spinner("검색 중..."):
                response = search_listings(params)

            listings = response.get("data") or []
            if not listings:
                st.info("조회된 청약정보가 없습니다.")
                return
            st.caption(f"검색 결과 {len(listings)}건 ({current_sort_label})")
            page = total_pages = total_count = None
        else:
            with st.spinner("불러오는 중..."):
                response = get_listings_page(self.current_page, PAGE_SIZE, current_sort)

            page_data = response.get("data") or {}
            listings = page_data.get("items") or []
            page = page_data.get("page", 1)
            total_pages = page_data.get("total_pages", 1)
            total_count = page_data.get("total_count", 0)

            # 공고를 지워서 페이지가 줄어든 경우처럼, 백엔드가 맞춰 준 페이지를 따라갑니다.
            # 주소창도 함께 정리해 두면 다시 새로고침해도 같은 화면이 나옵니다.
            # 값이 같아지면 더 이상 고치지 않으므로 화면이 반복해서 다시 실행되지 않습니다.
            if page != self.current_page:
                # 검색 조건은 그대로 두고 페이지 번호만 맞춥니다.
                # 조건을 빼먹으면 주소가 바뀌면서 검색이 풀립니다.
                st.query_params.from_dict(build_params(page, None, self.current_search))
                st.rerun()

            if not listings:
                st.info("조회된 청약정보가 없습니다.")
                return

            st.caption(
                f"총 {total_count}건  |  {page} / {total_pages} 페이지 ({current_sort_label})"
            )

        page_ids = [listing["id"] for listing in listings]

        # 고른 상태는 선택칸에서만 읽습니다. 따로 적어 두지 않아 어긋날 일이 없습니다.
        chosen = picked_ids(st.session_state, page_ids)
        allowed, reason = can_delete(chosen)

        select_column, clear_column, delete_column = st.columns([1, 1, 1])

        if select_column.button("전체 선택", use_container_width=True, key="bulk-select-all"):
            set_all(st.session_state, page_ids, True)
            st.rerun()

        if clear_column.button("선택 해제", use_container_width=True, key="bulk-clear"):
            set_all(st.session_state, page_ids, False)
            st.rerun()

        if delete_column.button(
            f"선택 삭제 ({len(chosen)})",
            type="primary",
            use_container_width=True,
            disabled=not allowed,
            key="bulk-delete-open",
        ):
            # 누르면 확인 창만 뜹니다. 이 버튼만으로는 아무것도 지워지지 않습니다.
            self.confirm_bulk_delete(chosen, listings)

        if chosen:
            st.caption(f":gray[{len(chosen)}건 선택됨 · 이 페이지에서 고른 공고만 지웁니다.]")

        for listing in listings:
            with st.container(border=True):
                # 같은 공고 안에 주택형이 여러 개라 공고명이 전부 같습니다.
                # 주택명을 앞세우고 공고명은 작게 둡니다.
                text_column, image_column = st.columns([3, 1], vertical_alignment="top")

                with text_column:
                    # 선택칸이 상태를 직접 들고 있습니다.
                    # 여기서 화면을 다시 그리라고 하지 않습니다.
                    # 중간에 멈추면 아직 안 그린 아래 카드들의 선택이 사라져,
                    # 하나를 풀었는데 나머지까지 줄줄이 풀립니다.
                    st.checkbox("선택", key=checkbox_key(listing["id"]))

                    st.markdown(f"#### {card_title(listing)}")
                    st.caption(f"#{listing['id']}  ·  {listing.get('title') or ''}")

                    summary = summary_line(listing)
                    if summary:
                        st.write(summary)

                    address = address_line(listing)
                    if address:
                        st.write(address)

                with image_column:
                    if listing.get("image_url"):
                        st.image(listing["image_url"], use_container_width=True)

                # 금액은 가장 먼저 확인하는 값이라 나란히 크게 둡니다.
                deposit_column, rent_column = st.columns(2)
                deposit_column.caption("보증금")
                deposit_column.markdown(f"**{format_won(listing.get('deposit'))}**")
                rent_column.caption("월세")
                rent_column.markdown(f"**{format_won(listing.get('monthly_rent'))}**")

                st.caption(period_line(listing))

                # 설명이 길어 목록이 늘어지므로 첫 줄만 보여 주고 접어 둡니다.
                # 사진도 여기 안에 둡니다. 카드마다 사진을 여러 장 펼쳐 놓으면
                # 목록이 사진으로 뒤덮여 오히려 훑기 어려워집니다.
                preview = description_preview(listing)
                images = image_list(listing)
                summary = preview or count_label(images)

                if summary:
                    with st.expander(f"상세 정보  ·  {summary}"):
                        if images:
                            st.caption(count_label(images))
                            # 스무 장까지 올 수 있어 한 줄에 넷씩 끊어 놓습니다.
                            for row in rows_of(images):
                                columns = st.columns(len(row))
                                for column, url in zip(columns, row):
                                    column.image(url, use_container_width=True)
                            st.divider()

                        # 줄바꿈 하나는 마크다운에서 공백이 되어 항목이 한 줄로 붙습니다.
                        # 줄마다 따로 그려 항목이 구분되게 합니다.
                        for line in description_lines(listing):
                            st.markdown(format_description_line(line))

                link_column, edit_column = st.columns(2)

                with link_column:
                    if (listing.get("source_url") or "").startswith("https://example.invalid/portfolio-demo/v1/"):
                        st.caption("시연용 가상 공고입니다. 실제 신청이나 원문 페이지는 없습니다.")
                    elif listing.get("source_url"):
                        st.link_button(
                            "공고 원문 보기",
                            listing["source_url"],
                            use_container_width=True,
                        )

                with edit_column:
                    # 수정 버튼을 누르면 이 공고 하나만 수정 화면으로 보여줍니다.
                    if st.button(
                        "수정",
                        use_container_width=True,
                        key=f"edit-listing-{listing['id']}",
                    ):
                        self.open_edit(listing["id"])

                with st.expander("이 공고 삭제"):
                    st.warning("삭제한 청약정보는 복구할 수 없습니다.")
                    delete_confirmed = st.checkbox(
                        "삭제에 동의합니다.",
                        key=f"delete-confirm-{listing['id']}",
                    )
                    if st.button(
                        "삭제",
                        type="primary",
                        disabled=not delete_confirmed,
                        use_container_width=True,
                        key=f"delete-listing-{listing['id']}",
                    ):
                        result = delete_listing(listing["id"])
                        st.session_state.listing_message = result.get(
                            "message", "청약정보를 삭제했습니다."
                        )
                        st.rerun()

        # 검색 결과일 때는 페이지 이동 버튼을 두지 않습니다.
        if total_pages is None:
            return

        st.divider()
        previous_column, input_column, go_column, next_column, info_column = st.columns(
            [1, 1.2, 1, 1, 2]
        )

        with previous_column:
            if st.button("이전", disabled=page <= 1, use_container_width=True, key="listing-page-prev"):
                self.go_to_page(page - 1)

        with input_column:
            # key에 현재 페이지를 넣어 두면 페이지가 바뀔 때마다 입력창이 새로 만들어집니다.
            # 그래서 이미 만들어진 위젯의 session_state를 건드리지 않아도
            # 입력창 번호가 항상 현재 페이지와 같아집니다.
            target_page = st.number_input(
                "페이지 번호",
                min_value=1,
                max_value=total_pages,
                value=page,
                step=1,
                label_visibility="collapsed",
                key=f"listing-page-input-{page}-{total_pages}",
            )

        with go_column:
            if st.button("이동", use_container_width=True, key="listing-page-go"):
                self.go_to_page(int(target_page))

        with next_column:
            if st.button("다음", disabled=page >= total_pages, use_container_width=True, key="listing-page-next"):
                self.go_to_page(page + 1)

        with info_column:
            st.markdown(
                f"<div style='padding-top:0.4rem'>현재 {page} / {total_pages} 페이지</div>",
                unsafe_allow_html=True,
            )


