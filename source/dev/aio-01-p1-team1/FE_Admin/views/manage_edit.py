"""관리자 공고 관리 화면의 역할별 구성 요소."""


import streamlit as st

from clients.listing_client import get_listing, update_listing
from core.api_client import BackendAPIError
from core.constants import SEOUL_DISTRICTS
from core.page_params import build_params


# 이미지 크기 제한입니다. 백엔드에서도 같은 값으로 다시 검사합니다.
MAX_IMAGE_SIZE = 5 * 1024 * 1024

# 한 페이지에 보여줄 공고 수입니다.
PAGE_SIZE = 10

# 고른 정렬 기준을 담아 둘 자리입니다.
SORT_STATE_KEY = "admin-listing-sort"

from views.manage_dates import to_date


class ListingEditView:
    def show_listing_edit(self, listing_id: int) -> None:
        """선택한 공고 하나만 수정 화면으로 보여줍니다.

        새로고침으로 들어온 경우에도 공고를 다시 조회해서 채웁니다.
        """

        # 주소창에 남은 ID가 이미 지워진 공고를 가리킬 수 있습니다.
        # 이때는 오류 화면 대신 안내를 띄우고 목록으로 되돌립니다.
        try:
            response = get_listing(listing_id)
        except BackendAPIError as error:
            st.warning(f"수정할 청약정보를 불러오지 못했습니다. 목록으로 돌아갑니다. ({error})")
            st.query_params.from_dict(build_params(self.current_page))
            if st.button("목록으로 돌아가기", key="edit-back-after-error"):
                st.rerun()
            return

        listing = response.get("data") or {}
        if not listing:
            st.warning("수정할 청약정보를 찾을 수 없습니다. 이미 삭제된 공고일 수 있습니다.")
            st.query_params.from_dict(build_params(self.current_page))
            if st.button("목록으로 돌아가기", key="edit-back-when-missing"):
                st.rerun()
            return

        st.subheader("청약정보 수정")

        # 자치구 목록에 없는 예전 값(예: "서울")이면 선택되지 않은 상태로 둡니다.
        current_location = listing.get("location")
        location_index = (
            SEOUL_DISTRICTS.index(current_location)
            if current_location in SEOUL_DISTRICTS
            else None
        )
        if location_index is None:
            st.warning(
                f"현재 자치구 값 '{current_location}'은 서울 25개 자치구 목록에 없습니다. "
                "저장하려면 자치구를 다시 골라 주세요."
            )

        if message := st.session_state.pop("image_delete_message", None):
            st.success(message)

        # 사진은 아래 수정 폼과 따로 다룹니다.
        # 사진을 만져도 폼에 입력해 둔 값은 그대로 남고,
        # 폼을 저장해도 사진은 건드리지 않습니다.
        self.show_listing_images(listing_id, listing)

        st.divider()

        with st.form("listing_edit_form"):
            title = st.text_input("공고 제목", value=listing.get("title") or "", key=f"edit-title-{listing_id}")
            housing_name = st.text_input(
                "주택명", value=listing.get("housing_name") or "", key=f"edit-housing-name-{listing_id}"
            )
            area_sqm = st.number_input(
                "면적(㎡)",
                min_value=0.01,
                value=float(listing.get("area_sqm") or 0.01),
                key=f"edit-area-sqm-{listing_id}",
            )
            recruitment_count = st.number_input(
                "모집 인원",
                min_value=1,
                step=1,
                value=int(listing.get("recruitment_count") or 1),
                key=f"edit-recruitment-count-{listing_id}",
            )
            location = st.selectbox(
                "지역(서울 자치구)",
                SEOUL_DISTRICTS,
                index=location_index,
                placeholder="자치구를 선택해 주세요",
                key=f"edit-location-{listing_id}",
            )
            detail_address = st.text_input(
                "상세주소 (선택)",
                value=listing.get("detail_address") or "",
                placeholder="예: 서울 강남구 도곡로 464",
                key=f"edit-detail-address-{listing_id}",
            )
            deposit = st.number_input(
                "보증금",
                min_value=0,
                step=10000,
                value=int(listing.get("deposit") or 0),
                key=f"edit-deposit-{listing_id}",
            )
            monthly_rent = st.number_input(
                "월세",
                min_value=0,
                step=10000,
                value=int(listing.get("monthly_rent") or 0),
                key=f"edit-monthly-rent-{listing_id}",
            )
            application_start_date = st.date_input(
                "신청 시작일",
                value=to_date(listing.get("application_start_date")),
                key=f"edit-start-date-{listing_id}",
            )
            application_end_date = st.date_input(
                "신청 종료일",
                value=to_date(listing.get("application_end_date")),
                key=f"edit-end-date-{listing_id}",
            )
            description = st.text_area(
                "상세 설명", value=listing.get("description") or "", key=f"edit-description-{listing_id}"
            )
            image_file = st.file_uploader(
                "새 이미지 (선택, 최대 5MB) - 고르지 않으면 기존 이미지를 그대로 둡니다",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"edit-image-{listing_id}",
            )

            source_url = st.text_input(
                "원문 URL", value=listing.get("source_url") or "", key=f"edit-source-url-{listing_id}"
            )

            # 두 버튼을 그냥 두면 세로로 쌓이므로, 목록 화면의 페이지 이동 버튼처럼
            # 컬럼으로 나누어 같은 줄에 놓습니다.
            save_column, cancel_column = st.columns(2)

            with save_column:
                saved = st.form_submit_button("저장", type="primary", use_container_width=True)

            with cancel_column:
                canceled = st.form_submit_button("취소", use_container_width=True)

        if canceled:
            self.close_edit()

        if not saved:
            return

        if not (
            title.strip()
            and housing_name.strip()
            and location
            and description.strip()
            and source_url.strip()
        ):
            st.error("공고 제목, 주택명, 자치구, 상세 설명, 원문 URL을 모두 입력해 주세요.")
            return

        if application_end_date < application_start_date:
            st.error("신청 종료일은 신청 시작일보다 빠를 수 없습니다.")
            return

        if image_file is not None and image_file.size > MAX_IMAGE_SIZE:
            st.error(
                f"이미지 크기는 5MB를 넘을 수 없습니다. "
                f"(선택한 파일: {image_file.size / 1024 / 1024:.1f}MB) "
                f"크기를 줄이거나 이미지를 빼고 저장해 주세요."
            )
            return

        payload = {
            "title": title.strip(),
            "housing_name": housing_name.strip(),
            "area_sqm": str(area_sqm),
            "recruitment_count": str(int(recruitment_count)),
            "location": location,
            "detail_address": detail_address.strip(),
            "deposit": str(int(deposit)),
            "monthly_rent": str(int(monthly_rent)),
            "application_start_date": application_start_date.isoformat(),
            "application_end_date": application_end_date.isoformat(),
            "description": description.strip(),
            "source_url": source_url.strip(),
        }

        with st.spinner("수정하는 중..."):
            result = update_listing(listing_id, payload, image_file)

        if result.get("success"):
            st.session_state.listing_message = result.get(
                "message", "청약정보가 수정되었습니다."
            )
            self.close_edit()
        else:
            # 실패했는데 목록으로 나가면 성공한 것처럼 보이므로 수정 화면에 머뭅니다.
            st.error(result.get("message", "청약정보 수정에 실패했습니다."))

