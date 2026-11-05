"""화면과 인증 상태에 의존하지 않는 백엔드 JSON 응답 해석입니다."""


def decode_response(response, error_type):
    """기존 오류 안내를 유지하며 잘못된 JSON 구조도 안전하게 처리합니다."""
    try:
        payload = response.json()
    except ValueError as error:
        raise error_type("백엔드가 올바른 JSON을 반환하지 않았습니다.") from error
    if not isinstance(payload, dict):
        raise error_type("백엔드가 올바른 JSON 객체를 반환하지 않았습니다.")
    if response.is_error:
        message = payload.get("message")
        message = message if isinstance(message, str) and message else "요청에 실패했습니다."
        details = payload.get("errors")
        if isinstance(details, list):
            fields = [
                f"{item.get('field', '')}: {item.get('message', '')}"
                for item in details if isinstance(item, dict)
            ]
            if fields:
                message += " " + "; ".join(fields)
        raise error_type(f"{message} ({response.status_code})")
    return payload
