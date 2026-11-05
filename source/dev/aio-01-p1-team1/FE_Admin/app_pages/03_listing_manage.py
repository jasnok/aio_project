import streamlit as st
from streamlit.components.v1 import html as components_html
from core.api_client import BackendAPIError
from core.auth import is_logged_in
from core.page_params import SEARCH_KEYS, build_params, parse_edit_id, parse_page, parse_search
from core.ui import page_header
from views.listing_management import ListingManagement

page_header("📋", "청약정보 조회 / 삭제", "등록된 공고를 검색하고 대량 삭제할 수 있습니다.")

if not is_logged_in():
    st.warning("로그인이 필요합니다.")
    st.stop()

if message := st.session_state.pop("listing_message", None):
    st.success(message)

# 지금 보고 있는 페이지와 수정 중인 공고는 주소창(query parameter)에 둡니다.
# st.session_state에 두면 브라우저를 새로고침할 때 사라지기 때문입니다.
# 로그인 정보는 여기 넣지 않습니다. 그건 Session Storage가 따로 맡습니다.
current_page = parse_page(st.query_params.get_all("page"))
current_edit_id = parse_edit_id(st.query_params.get_all("edit_id"))
# 조건검색도 주소창에 둡니다. 수정 화면에 다녀와도 보던 검색 결과가 남습니다.
current_search = parse_search(
    {name: st.query_params.get_all(name) for name in SEARCH_KEYS}
)

# "page=abc"나 "edit_id=-1"처럼 이상한 값이 들어오면 위에서 안전한 값으로 바꿉니다.
# 주소창도 그 값으로 정리해 두어야 다시 새로고침해도 같은 화면이 나옵니다.
# 한 번 정리하면 값이 같아지므로 화면이 반복해서 다시 실행되지 않습니다.
# 브라우저 뒤로가기는 주소만 바꿀 뿐, Streamlit이 스스로 화면을 다시 그리지 않습니다.
# 그래서 주소는 목록인데 화면은 수정 화면에 그대로 남습니다.
# 주소가 바뀌면(popstate) 화면을 다시 읽어 오도록 한 번만 알려 둡니다.
# 다시 읽어 오므로 저장하지 않은 수정 입력값은 남지 않습니다.
components_html(
    """
    <script>
    (function () {
      const page = window.parent;
      if (page.__listingHistorySyncReady) return;
      page.__listingHistorySyncReady = true;
      page.addEventListener("popstate", function () {
        page.location.reload();
      });
    })();
    </script>
    """,
    height=0,
)

_canonical_params = build_params(current_page, current_edit_id, current_search)

# 값이 이미 같으면 절대로 다시 쓰지 않습니다.
# st.query_params.from_dict()는 같은 값을 써도 브라우저 방문 기록을 새로 쌓습니다.
# 화면이 다시 그려질 때마다 쓰면 같은 주소가 기록에 여러 번 남아,
# 뒤로가기를 눌러도 똑같은 수정 화면으로 되돌아와 제자리에 멈춘 것처럼 보입니다.
if st.query_params.to_dict() != _canonical_params:
    st.query_params.from_dict(_canonical_params)
    st.rerun()


view = ListingManagement(current_page, current_edit_id, current_search)
try:
    if current_edit_id is None:
        view.show_listing_list()
    else:
        view.show_listing_edit(current_edit_id)
except BackendAPIError as error:
    st.error(str(error))
