"""관리자 공고 관리 화면의 역할별 구성 요소."""


import streamlit as st

from clients.listing_client import delete_listing, replace_listing_images
from core.api_client import BackendAPIError
from core.bulk_delete import checkbox_key, names_of, summarize_deletes
from core.image_delete import summarize_result
from core.image_gallery import (
    MAX_IMAGE_COUNT,
    check_upload,
    count_label,
    image_list,
    rows_of,
)


# 이미지 크기 제한입니다. 백엔드에서도 같은 값으로 다시 검사합니다.
MAX_IMAGE_SIZE = 5 * 1024 * 1024

# 한 페이지에 보여줄 공고 수입니다.
PAGE_SIZE = 10

# 고른 정렬 기준을 담아 둘 자리입니다.
SORT_STATE_KEY = "admin-listing-sort"



class ListingImagesView:
    @st.dialog("사진 삭제 확인")
    def confirm_one_image_delete(self, listing_id: int, images: list[str], target: str) -> None:
        """사진 한 장을 지우기 전에 한 번 더 묻는 경고창입니다.

        남길 사진 목록을 서버에 보내는 방식이라, 여기서 삭제를 고르기 전까지는
        아무것도 보내지 않습니다.
        """

        st.image(target, width=240)
        st.write("이 사진을 삭제하시겠습니까?")
        st.warning("삭제된 사진은 복구할 수 없습니다.")
        st.caption("공고의 다른 수정 내용은 저장되지 않으며 이 사진만 삭제됩니다.")

        cancel_column, delete_column = st.columns(2)

        with cancel_column:
            if st.button("취소", use_container_width=True, key="one-image-cancel"):
                st.rerun()

        with delete_column:
            if st.button(
                "삭제", type="primary", use_container_width=True, key="one-image-confirm"
            ):
                kept = [url for url in images if url != target]
                try:
                    response = replace_listing_images(listing_id, kept, [])
                except BackendAPIError as error:
                    st.error(str(error))
                    return

                succeeded, message = summarize_result(response)
                if not succeeded:
                    st.error(message)
                    return

                st.session_state.image_delete_message = message
                st.rerun()


    @st.dialog("선택한 공고 삭제 확인")
    def confirm_bulk_delete(self, chosen: list[int], listings: list) -> None:
        """고른 공고를 지우기 전에 무엇을 지우는지 보여 줍니다.

        지우는 일은 되돌릴 수 없어, 이름을 하나씩 늘어놓고 다시 묻습니다.
        여기서 삭제를 고르기 전까지는 서버에 아무것도 보내지 않습니다.
        """

        st.write(f"아래 {len(chosen)}건을 삭제하시겠습니까?")
        st.warning("삭제한 청약정보와 사진은 복구할 수 없습니다.")

        with st.container(height=220, border=True):
            for line in names_of(chosen, listings):
                st.caption(line)

        cancel_column, delete_column = st.columns(2)

        with cancel_column:
            if st.button("취소", use_container_width=True, key="bulk-delete-cancel"):
                st.rerun()

        with delete_column:
            if st.button(
                "삭제", type="primary", use_container_width=True, key="bulk-delete-confirm"
            ):
                succeeded, failed = [], []
                progress = st.progress(0.0, text="삭제하는 중...")

                for done, listing_id in enumerate(chosen, start=1):
                    try:
                        response = delete_listing(listing_id)
                        ok, _ = summarize_result(response)
                        (succeeded if ok else failed).append(listing_id)
                    except BackendAPIError:
                        failed.append(listing_id)
                    progress.progress(done / len(chosen), text=f"{done}/{len(chosen)}건 처리")

                # 지운 공고는 선택에서 뺍니다. 실패한 것만 남겨 다시 시도할 수 있게 합니다.
                # 지운 공고의 선택칸을 끕니다. 실패한 것은 켜 두어 다시 시도할 수 있게 합니다.
                for listing_id in succeeded:
                    st.session_state[checkbox_key(listing_id)] = False
                st.session_state.listing_message = summarize_deletes(succeeded, failed)
                st.rerun()


    def show_listing_images(self, listing_id: int, listing: dict) -> None:
        """공고 사진을 보여 주고 더하거나 지웁니다.

        아래 수정 폼과 따로 둡니다. 사진을 정리할 때 폼에 입력만 해 두고
        아직 저장하지 않은 제목·금액 같은 값이 함께 저장되지 않게 하려는 것입니다.
        """

        images = image_list(listing)

        st.caption(f"현재 사진  ·  {count_label(images) or '없음'}")

        if images:
            for row in rows_of(list(enumerate(images))):
                columns = st.columns(len(row))
                for column, (index, url) in zip(columns, row):
                    column.image(url, use_container_width=True)
                    # 맨 앞 사진이 목록 카드에 보이는 대표 이미지입니다.
                    if index == 0:
                        column.caption("대표 이미지")
                    if column.button(
                        "삭제",
                        use_container_width=True,
                        key=f"image-remove-{listing_id}-{index}",
                    ):
                        self.confirm_one_image_delete(listing_id, images, url)
        else:
            st.caption("등록된 사진이 없습니다.")

        remaining = MAX_IMAGE_COUNT - len(images)
        if remaining <= 0:
            st.info(f"사진은 최대 {MAX_IMAGE_COUNT}장까지입니다. 더 넣으려면 먼저 지워 주세요.")
            return

        new_files = st.file_uploader(
            f"사진 추가 (최대 {remaining}장 더)",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            key=f"edit-image-add-{listing_id}-{st.session_state.get(f'image-upload-version-{listing_id}', 0)}",
        )
        new_files = new_files or []

        problem = check_upload(new_files, already=len(images))
        if problem:
            st.error(problem)

        if st.button(
            "사진 저장",
            disabled=not new_files or bool(problem),
            key=f"image-add-save-{listing_id}",
        ):
            try:
                with st.spinner(f"사진 {len(new_files)}장을 업로드하는 중..."):
                    response = replace_listing_images(listing_id, images, new_files)
            except BackendAPIError as error:
                st.error(str(error))
                return

            succeeded, message = summarize_result(response)
            if not succeeded:
                st.error(message)
                return

            st.session_state.image_delete_message = message
            version_key = f"image-upload-version-{listing_id}"
            st.session_state[version_key] = st.session_state.get(version_key, 0) + 1
            st.rerun()


