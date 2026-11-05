"""화면에 제공하는 명확한 사이트 사용법 질문과 서버의 고정 안내 분류입니다."""

SITE_GUIDE_FAQ = {
    "내 정보는 어디서 확인할 수 있나요?": "PROFILE_VIEW",
    "닉네임을 수정하려면 어떻게 하나요?": "PROFILE_EDIT",
    "청약 공고는 어떻게 검색하나요?": "LISTING_SEARCH",
    "관심 있는 공고를 즐겨찾기에 추가하려면 어떻게 하나요?": "FAVORITE_ADD",
    "저장한 즐겨찾기는 어디에서 확인하나요?": "FAVORITE_VIEW",
    "아이디를 변경할 수 있나요?": "ACCOUNT_ID_CHANGE",
    "비밀번호는 어떻게 변경하나요?": "PASSWORD_CHANGE",
    "AI 채팅 상담은 어떻게 이용하나요?": "AI_CHAT_USAGE",
    "AI 안내원에게 어떤 질문을 할 수 있나요?": "AI_GUIDE_SCOPE",
}

EXAMPLE_QUESTIONS = (*SITE_GUIDE_FAQ, "보증금이 무엇인가요?")
