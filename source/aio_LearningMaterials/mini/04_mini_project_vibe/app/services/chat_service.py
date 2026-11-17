"""Google Gen AI SDK를 사용해 Gemini 응답을 생성합니다."""

from google import genai

from app.core.chat_config import get_gemini_api_key, get_gemini_model
from app.schemas.chat_schema import ChatResponse


class ChatConfigurationError(Exception):
    """Gemini 환경변수가 올바르지 않을 때 발생합니다."""


class ChatServiceError(Exception):
    """Gemini 외부 호출에 실패했을 때 발생합니다."""


def generate_chat_response(message: str) -> ChatResponse:
    """사용자 메시지를 Gemini에 보내고 정형화된 응답을 반환합니다."""

    try:
        api_key = get_gemini_api_key()
        model = get_gemini_model()
    except RuntimeError as exc:
        raise ChatConfigurationError from exc

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model, contents=message)
        answer = (response.text or "").strip()
        if not answer:
            raise ChatServiceError
        return ChatResponse(answer=answer, model=model)
    except ChatServiceError:
        raise
    except Exception as exc:
        raise ChatServiceError from exc
