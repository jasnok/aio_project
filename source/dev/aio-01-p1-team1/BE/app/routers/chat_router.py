"""독립 실행과 최종 앱에서 함께 사용할 AI 상담 API입니다."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.api_response import ApiResponse
from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.core.workflow_trace import traced_workflow
from app.schemas.chat_schema import ChatRequest, ChatSaveRequest, ChatSummarySaveResult
from app.services.chat_service import (
    create_chat_answer,
    create_chat_summary,
    delete_chat_summary,
    get_chat_profile,
    get_chat_summary,
    get_summary_storage_mode,
    list_chat_summaries,
)
from app.services.chat_history_service import (
    append_chat_exchange,
    clear_summarized_history,
    delete_chat_history,
    get_chat_history,
    get_chat_snapshot,
)


chat_router = APIRouter(prefix="/chat", tags=["Chat"])


@chat_router.get("/health")
def health() -> ApiResponse:
    return ApiResponse(
        success=True,
        message="AI 상담 테스트 API가 실행 중입니다.",
        data={"summary_storage": get_summary_storage_mode()},
    )


@chat_router.get("/me")
def me(user: AuthenticatedUser = Depends(get_current_user)) -> ApiResponse:
    return ApiResponse(
        success=True,
        message="상담 사용자 정보를 조회했습니다.",
        data=get_chat_profile(user.id, user.email),
    )


@chat_router.post("/message")
def message(
    request: ChatRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> ApiResponse:
    with traced_workflow("chat_answer") as trace:
        with trace.stage("history.read"):
            snapshot = get_chat_snapshot(user.id)
            history = snapshot.messages
        answer = create_chat_answer(history, request.question, trace=trace)
        with trace.stage("history.append"):
            append_chat_exchange(user.id, request.question, answer.answer, expected_history=history, expected_revision=snapshot.revision)
        return ApiResponse(success=True, message="AI 상담 답변을 생성했습니다.", data=answer)


@chat_router.get("/history")
def history(user: AuthenticatedUser = Depends(get_current_user)) -> ApiResponse:
    messages = get_chat_history(user.id)
    return ApiResponse(
        success=True,
        message="진행 중인 상담을 조회했습니다.",
        data=messages,
    )


@chat_router.delete("/history")
def clear_history(user: AuthenticatedUser = Depends(get_current_user)) -> ApiResponse:
    delete_chat_history(user.id)
    return ApiResponse(success=True, message="진행 중인 상담을 종료했습니다.", data=None)


@chat_router.post("/save")
def save(
    request: ChatSaveRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> ApiResponse:
    with traced_workflow("chat_summary") as trace:
        with trace.stage("history.read"):
            snapshot = get_chat_snapshot(user.id)
            history = snapshot.messages
        with trace.stage("summary.lookup"):
            existing = get_chat_summary(user.id, request.request_id) if request.request_id else None
        if existing:
            with trace.stage("summary.recover"):
                result = ChatSummarySaveResult(**existing.model_dump(), remaining_messages=history)
            return ApiResponse(success=True, message="이미 저장된 상담 요약을 확인했습니다. 진행 중인 기록은 보존했습니다.", data=result)
        summary = create_chat_summary(user.id, history, summary_id=request.request_id, trace=trace)
        with trace.stage("history.cleanup"):
            remaining = clear_summarized_history(user.id, history, expected_revision=snapshot.revision)
        result = ChatSummarySaveResult(**summary.model_dump(), remaining_messages=remaining)
        message = "상담 요약 미리보기를 저장했습니다."
        if remaining:
            message += " 요약 중 대화가 변경되어 진행 중인 기록은 보존했습니다."
        return ApiResponse(success=True, message=message, data=result)


@chat_router.get("/summaries")
def summaries(user: AuthenticatedUser = Depends(get_current_user)) -> ApiResponse:
    items = list_chat_summaries(user.id)
    return ApiResponse(success=True, message="저장된 상담 요약을 조회했습니다.", data=items)


@chat_router.delete("/summaries/{summary_id}")
def remove_summary(
    summary_id: UUID,
    user: AuthenticatedUser = Depends(get_current_user),
) -> ApiResponse:
    delete_chat_summary(user.id, str(summary_id))
    return ApiResponse(success=True, message="저장된 상담을 삭제했습니다.", data=None)
