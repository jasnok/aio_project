import streamlit as st
from clients import listing_client
from core.api_client import BackendAPIError
from core.extracted_image import _UploadedImage

def register_selected(results, selected_indexes, picked_by_index, found_images):
    st.divider()

    if st.button(
        f"선택한 {len(selected_indexes)}건 등록",
        type="primary",
        disabled=not selected_indexes,
    ):
        by_index = {result["index"]: result for result in results}
        succeeded, failed = [], []

        # 등록할 건들이 실제로 쓰는 사진만 한 번씩 올립니다.
        # 공고건마다 올리면 같은 파일이 여러 벌 쌓입니다.
        # 여러 공고가 같은 사진을 가리켜도 파일은 하나입니다.
        needed = sorted(
            {
                image_index
                for index in selected_indexes
                for image_index in picked_by_index.get(index, [])
            }
        )

        # 사진 자리 번호 -> 올리고 받은 주소
        url_by_image: dict[int, str] = {}

        if needed:
            try:
                with st.spinner(f"사진 {len(needed)}장을 올리는 중..."):
                    response = listing_client.upload_listing_images(
                        [_UploadedImage(found_images[i]) for i in needed]
                    )
                uploaded = (response.get("data") or {}).get("image_urls") or []
                url_by_image = dict(zip(needed, uploaded))
            except BackendAPIError as error:
                st.error(f"사진을 올리지 못했습니다. 사진 없이 등록합니다. ({error})")

        with st.spinner("등록하는 중..."):
            for index in selected_indexes:
                payload = dict(by_index[index]["payload"])

                # 이 공고건이 고른 사진만 붙입니다. 첫 장이 대표 이미지가 됩니다.
                urls = [
                    url_by_image[i]
                    for i in picked_by_index.get(index, [])
                    if i in url_by_image
                ]
                payload["image_urls"] = urls
                payload["image_url"] = urls[0] if urls else None
                label = payload["housing_name"]
                try:
                    response = listing_client.create_listing(payload)
                    if response.get("success"):
                        succeeded.append(label)
                        registered = set(st.session_state.get("auto_registered", set()))
                        registered.add(index)
                        st.session_state.auto_registered = registered
                    else:
                        failed.append((label, response.get("message", "등록에 실패했습니다.")))
                except BackendAPIError as error:
                    failed.append((label, str(error)))
                    # 한 건이라도 실패하면 멈춥니다. 남은 건은 원인을 확인한 뒤 다시 시도합니다.
                    break

        if succeeded:
            st.success(f"{len(succeeded)}건을 등록했습니다.")
            for name in succeeded:
                st.caption(f"• {name}")

        if failed:
            st.error(f"{len(failed)}건을 등록하지 못했습니다.")
            for name, reason in failed:
                st.caption(f"• {name}: {reason}")

        if succeeded and not failed:
            # 같은 PDF를 두 번 등록하지 않도록 결과를 비웁니다.
            st.session_state.pop("auto_extracted", None)

    if st.button("추출 결과 지우기", key="auto-clear"):
        st.session_state.pop("auto_extracted", None)
        st.session_state.pop("auto_source_name", None)
        st.rerun()
