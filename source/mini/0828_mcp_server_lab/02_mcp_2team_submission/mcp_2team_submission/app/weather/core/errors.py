"""Weather MCP에서 사용하는 도메인 예외입니다."""


class WeatherProviderError(RuntimeError):
    """기상정보 외부 API 호출에 실패한 경우 발생합니다."""
