"""Tour MCP에서 사용하는 도메인 예외입니다."""


class ConfigurationError(RuntimeError):
    """필수 환경설정이 없거나 잘못된 경우 발생합니다."""


class EmbeddingProviderError(RuntimeError):
    """임베딩 Provider 호출 또는 응답 검증에 실패했습니다."""
