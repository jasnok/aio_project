import streamlit as st
from core.page_params import build_params
from views.manage_images import ListingImagesView
from views.manage_list import ListingListView
from views.manage_edit import ListingEditView

class ListingManagement(ListingImagesView, ListingListView, ListingEditView):
    def __init__(self, page, edit_id, search):
        self.current_page = page
        self.current_edit_id = edit_id
        self.current_search = search

    def go_to_page(self, page: int) -> None:
        """페이지를 옮깁니다. 열려 있던 수정 폼은 닫고, 검색 조건은 유지합니다."""
        st.query_params.from_dict(build_params(page, None, self.current_search))
        st.rerun()


    def open_edit(self, listing_id: int) -> None:
        """수정 화면을 엽니다. 보고 있던 페이지 번호와 검색 조건은 그대로 둡니다."""
        st.query_params.from_dict(build_params(self.current_page, listing_id, self.current_search))
        st.rerun()


    def close_edit(self) -> None:
        """수정 화면을 닫고 목록으로 돌아갑니다. 페이지 번호와 검색 조건은 유지합니다."""
        st.query_params.from_dict(build_params(self.current_page, None, self.current_search))
        st.rerun()


