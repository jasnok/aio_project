# 08_listing_auto_create.py
"""공고 PDF를 Gemini에 보내 청약정보를 뽑아내고, 확인한 뒤 등록합니다.

뽑아낸 값을 바로 저장하지 않습니다. 관리자가 화면에서 확인하고 고른 건만
기존 청약정보 등록 API로 보냅니다.
"""

from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from clients.gemini_client import (
    GeminiError,
    extract_listings_from_pdf,
    identify_images,
)
from core.auto_demo import sample_analysis
from core.auto_state import store_analysis
from views.auto_review import render_review
from core.auth import is_logged_in
from core.document_images import extract_images
from core.gemini_config import get_model_name, has_api_key
from core.ui import page_header


# 공고 파일 크기 제한입니다. 너무 큰 파일은 모델이 처리하지 못합니다.
MAX_PDF_SIZE = 20 * 1024 * 1024



page_header(
    "🤖",
    "청약정보 등록(자동)",
    "가상 샘플이나 PDF/HWPX 분석 결과를 검토하고 등록하세요.",
)

if not is_logged_in():
    st.warning("로그인이 필요합니다.")
    st.stop()

st.caption("분석 결과를 검토하고 고른 건만 등록합니다.")

demo_mode = st.radio(
    "분석 방식",
    ["가상 샘플 재생", "Gemini로 실제 문서 분석"],
    horizontal=True,
    key="auto-analysis-mode",
)

if demo_mode == "가상 샘플 재생":
    st.info(
        "미리 저장한 가상 분석 결과를 불러옵니다. AI가 업로드한 문서를 읽는 기능이 아니며 "
        "실제 모집 공고도 아닙니다. 결과 검토와 등록 화면을 키 없이 시연할 수 있습니다."
    )
    st.caption("샘플 원문 기준: 월세 280,000원. 누락된 월세를 입력해 검토 과정을 시연하세요.")
    if st.button("가상 분석 결과 불러오기", type="primary"):
        store_analysis(sample_analysis(), "포트폴리오 가상 샘플", [], [], "sample")
else:
    st.caption(f"사용 모델: {get_model_name()}")
    if not has_api_key():
        st.error("Gemini API 키가 없습니다. `FE_Admin/.env`에 `GEMINI_API_KEY`를 설정하세요.")
        st.stop()
    st.warning("실제 문서 분석은 Gemini API를 호출합니다. 개인정보가 없는 문서만 사용하세요.")
    pdf_file = st.file_uploader("공고 파일 (PDF 또는 HWPX)", type=["pdf", "hwpx"], key="auto-pdf")

if demo_mode == "Gemini로 실제 문서 분석" and st.button("공고에서 청약정보 뽑아내기", type="primary", disabled=pdf_file is None):
    if pdf_file.size > MAX_PDF_SIZE:
        st.error(
            f"공고 파일 크기는 20MB를 넘을 수 없습니다. "
            f"(선택한 파일: {pdf_file.size / 1024 / 1024:.1f}MB)"
        )
    else:
        raw = pdf_file.getvalue()

        # 사진은 파일에서 직접 꺼냅니다. AI가 필요 없는 일입니다.
        # 실패해도 청약정보 추출은 계속합니다. 사진은 나중에 손으로 올릴 수 있습니다.
        try:
            found_images = extract_images(raw, pdf_file.name)
        except Exception as error:
            found_images = []
            st.warning(f"사진을 꺼내지 못했습니다. 청약정보만 뽑습니다. ({type(error).__name__})")

        try:
            # 두 분석의 입력은 독립적이므로 동시에 요청합니다.
            #   1) 공고 파일에서 청약정보 뽑기
            #   2) 꺼낸 사진마다 어느 주택 것인지 알아내기
            with st.spinner("Gemini가 공고와 사진을 읽는 중입니다..."):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    listing_job = pool.submit(extract_listings_from_pdf, raw, pdf_file.name)
                    label_job = pool.submit(identify_images, found_images)
                    extracted = listing_job.result()
                    image_labels_found = label_job.result()

            store_analysis(extracted, pdf_file.name, found_images, image_labels_found, "gemini")
        except GeminiError as error:
            st.error(str(error))

extracted = st.session_state.get("auto_extracted")
expected_mode = "sample" if demo_mode == "가상 샘플 재생" else "gemini"
if st.session_state.get("auto_result_mode") != expected_mode:
    extracted = None

if extracted and st.session_state.get("auto_result_mode") == "sample":
    st.info("현재 결과는 저장된 가상 샘플입니다. 실제 AI 분석 결과가 아닙니다.")

if not extracted:
    st.stop()

render_review(extracted)
