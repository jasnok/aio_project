import streamlit as st
from core.constants import SEOUL_DISTRICTS
from core.image_gallery import rows_of
from core.image_matching import one_house_only, suggest_matches
from core.listing_extract import FIXABLE_DATE_FIELDS, FIXABLE_NUMBER_FIELDS, SHARED_TEXT_FIELDS, missing_shared_fields, summarize, unreadable_fields, validate_all

from views.auto_registration import register_selected

def render_review(extracted):
    # 화면에서 손으로 채운 값이 있으면 덮어씁니다.
    # 모델이 못 읽은 칸을 관리자가 채우면 그 값으로 다시 확인합니다.
    fixes = st.session_state.get("auto_fixes") or {}
    patched = []
    for index, item in enumerate(extracted):
        merged = dict(item) if isinstance(item, dict) else item
        if isinstance(merged, dict) and index in fixes:
            merged.update(fixes[index])
        patched.append(merged)

    # 공고 전체에 하나뿐인 값은 여기서 한 번만 받습니다.
    # 원문 주소가 문서에 없는 공고가 있어, 건마다 넣게 하면 번거롭습니다.
    shared = st.session_state.get("auto_shared") or {}
    if shared:
        for merged in patched:
            if isinstance(merged, dict):
                for field, value in shared.items():
                    if value:
                        merged[field] = value

    results = validate_all(patched, SEOUL_DISTRICTS)
    counts = summarize(results)

    st.divider()
    st.subheader(f"추출 결과 {counts['total']}건")

    ready_column, blocked_column = st.columns(2)
    ready_column.metric("등록 가능", f"{counts['ready']}건")
    blocked_column.metric("확인 필요", f"{counts['blocked']}건")

    if counts["blocked"]:
        st.warning(
            "값이 비어 있거나 형식이 맞지 않는 건이 있습니다. "
            "공고문 표에서 칸이 병합되어 있으면 값을 읽지 못하는 일이 있습니다. "
            "아래에서 그 값을 직접 채우면 함께 등록할 수 있습니다."
        )

    missing_shared = missing_shared_fields(patched)
    if missing_shared:
        with st.container(border=True):
            st.markdown("**공고 전체에 넣을 값**")
            st.caption(
                "문서에서 찾지 못한 값입니다. 한 번만 넣으면 모든 건에 함께 들어갑니다."
            )
            entered_shared = {}
            for field, title in SHARED_TEXT_FIELDS:
                if field not in missing_shared:
                    continue
                entered_shared[field] = st.text_input(
                    title,
                    placeholder="예: https://www.geumcheon.go.kr/...",
                    key=f"auto-shared-{field}",
                )

            if st.button("모든 건에 적용", key="auto-shared-apply"):
                saved = dict(st.session_state.get("auto_shared") or {})
                saved.update({k: v.strip() for k, v in entered_shared.items()})
                st.session_state.auto_shared = saved
                st.rerun()

    found_images = st.session_state.get("auto_images") or []

    # 사진에 붙일 이름표입니다. 아래 공고건마다 이 이름으로 고릅니다.
    def _image_label(index: int, image: dict) -> str:
        """사진 고르는 칸에 보여 줄 이름입니다.

        Gemini가 알아낸 주택명이 있으면 함께 적어, 무엇을 고르는지 알 수 있게 합니다.
        """
        where = f"{image['page']}쪽" if image.get("page") else f"{index + 1}번째"
        labels = st.session_state.get("auto_image_labels") or []
        found = labels[index] if index < len(labels) else {}
        name = (found.get("house_name") or "").strip()
        kind = (found.get("kind") or "").strip()
        tail = f" — {name}" if name else (f" — {kind}" if kind else "")
        return f"{index + 1}. {where}{tail}"


    image_labels = [_image_label(i, im) for i, im in enumerate(found_images)]

    if found_images:
        st.divider()
        st.subheader(f"공고에서 꺼낸 사진 {len(found_images)}장")
        st.caption(
            "아래 공고건마다 붙일 사진을 고릅니다. "
            "여기서는 어떤 사진이 몇 번인지만 확인하세요."
        )

        for row in rows_of([str(i) for i in range(len(found_images))]):
            columns = st.columns(len(row))
            for column, key in zip(columns, row):
                index = int(key)
                image = found_images[index]
                column.image(image["data"], use_container_width=True)
                column.caption(image_labels[index])

    # 공고건마다 붙일 사진을 미리 골라 둡니다. 화면에서 바꿀 수 있습니다.
    found_labels = st.session_state.get("auto_image_labels") or []
    suggested = suggest_matches(results, found_images, found_labels)
    single_house = one_house_only(results)

    st.divider()
    st.subheader("등록할 청약정보")

    if found_images:
        if single_house:
            st.caption(
                "이 공고는 주택이 한 곳이라 꺼낸 사진을 모두 붙여 두었습니다."
            )
        else:
            st.caption(
                "주택이 여러 곳이라, 사진에 적힌 주택 이름을 읽어 미리 골라 두었습니다. "
                "맞지 않으면 바꿔 주세요."
            )

    selected_indexes = []
    # 공고건마다 고른 사진의 자리 번호를 담습니다.
    picked_by_index: dict[int, list[int]] = {}

    for result in results:
        source = result["source"]
        label = source.get("housing_name") or source.get("title") or f"{result['index'] + 1}번째 항목"

        with st.container(border=True):
            if result["index"] in st.session_state.get("auto_registered", set()):
                st.success(f"{label} — 등록 완료")
                continue
            if result["problems"]:
                st.markdown(f"**{label}** — 확인 필요")
                for problem in result["problems"]:
                    st.caption(f"• {problem}")

                # 모델이 못 읽은 칸만 보여 주고 직접 채우게 합니다.
                # 공고문 표에서 칸이 병합되어 있으면 값을 읽지 못하는 일이 생깁니다.
                bad = unreadable_fields(result["source"])
                if bad:
                    st.caption(":gray[공고문을 보고 아래 값을 채우면 등록할 수 있습니다.]")
                    entered = {}
                    for field, title in FIXABLE_NUMBER_FIELDS:
                        if field not in bad:
                            continue
                        step = 0.01 if field == "area_sqm" else 1
                        entered[field] = st.number_input(
                            title,
                            min_value=0.0 if field == "area_sqm" else 0,
                            step=step,
                            key=f"auto-fix-{result['index']}-{field}",
                        )
                    for field, title in FIXABLE_DATE_FIELDS:
                        if field not in bad:
                            continue
                        entered[field] = st.date_input(
                            title, key=f"auto-fix-{result['index']}-{field}"
                        ).isoformat()

                    if st.button("이 값으로 다시 확인", key=f"auto-fixgo-{result['index']}"):
                        saved = dict(st.session_state.get("auto_fixes") or {})
                        saved[result["index"]] = entered
                        st.session_state.auto_fixes = saved
                        st.rerun()
            else:
                payload = result["payload"]
                checked = st.checkbox(
                    f"{label}", value=True, key=f"auto-pick-{result['index']}"
                )
                if checked:
                    selected_indexes.append(result["index"])
                st.caption(
                    f"{payload['location']}  ·  전용 {payload['area_sqm']}㎡  ·  "
                    f"{payload['recruitment_count']}호 모집"
                )
                st.caption(
                    f"보증금 {payload['deposit']:,}원  |  월세 {payload['monthly_rent']:,}원  |  "
                    f"신청 {payload['application_start_date']} ~ {payload['application_end_date']}"
                )

                if found_images:
                    # 주택이 한 곳뿐이면 꺼낸 사진을 모두 붙입니다.
                    # 여러 곳이면 쪽 번호로 미리 골라 둔 것을 처음 값으로 씁니다.
                    default = (
                        list(range(len(found_images)))
                        if single_house
                        else suggested.get(result["index"], [])
                    )
                    chosen = st.multiselect(
                        "붙일 사진",
                        options=list(range(len(found_images))),
                        default=default,
                        format_func=lambda i: image_labels[i],
                        key=f"auto-imgpick-{result['index']}",
                    )
                    picked_by_index[result["index"]] = chosen
                    if not chosen:
                        st.caption(":gray[사진 없이 등록됩니다.]")

            with st.expander("뽑아낸 원본 값 보기"):
                st.json(source)

    register_selected(results, selected_indexes, picked_by_index, found_images)
