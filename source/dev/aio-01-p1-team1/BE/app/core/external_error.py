"""외부 라이브러리의 원본 오류를 노출하지 않는 서비스별 안내."""
import httpx
from fastapi import HTTPException


class ExternalServiceError(HTTPException):
    def __init__(self, service, reason, message, status_code):
        self.service = service
        self.reason = reason
        super().__init__(status_code=status_code, detail=message)


def invalid_ai_response(label="AI 상담"):
    return ExternalServiceError("gemini", "invalid_response", f"{label} 결과의 형식을 확인할 수 없습니다. 다시 시도해 주세요.", 502)


def ai_error(error, label="AI 상담"):
    code = getattr(error, "code", None) or getattr(error, "status_code", None)
    if str(code) == "429":
        return ExternalServiceError("gemini", "rate_limit", f"{label} 호출 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.", 503)
    if str(code) in ("401", "403"):
        return ExternalServiceError("gemini", "configuration", f"{label} 연결 설정을 확인해야 합니다. 관리자에게 문의해 주세요.", 503)
    if isinstance(error, RuntimeError):
        return ExternalServiceError("gemini", "configuration", f"{label} 실행 설정을 확인해야 합니다. 관리자에게 문의해 주세요.", 503)
    if isinstance(error, (TimeoutError, httpx.TimeoutException)):
        return ExternalServiceError("gemini", "timeout", f"{label} 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.", 504)
    return ExternalServiceError("gemini", "unavailable", f"{label} 답변을 생성하지 못했습니다. 잠시 후 다시 시도해 주세요.", 502)
