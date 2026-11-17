"""Gemini Chat HTTP API입니다."""

from fastapi import APIRouter, HTTPException

from app.core.api_response import ApiResponse
from app.schemas.chat_schema import ChatRequest
from app.services.chat_service import ChatConfigurationError, ChatServiceError, generate_chat_response


chat_router = APIRouter(prefix="/chat", tags=["Chat"])


@chat_router.post("/gemini")
def chat_with_gemini(request: ChatRequest) -> ApiResponse:
    try:
        data = generate_chat_response(request.message)
    except ChatConfigurationError:
        raise HTTPException(status_code=500, detail="Gemini API 설정이 필요합니다.") from None
    except ChatServiceError:
        raise HTTPException(status_code=502, detail="Gemini 응답을 생성하지 못했습니다.") from None
    return ApiResponse(success=True, message="Gemini 응답을 생성했습니다.", data=data)
