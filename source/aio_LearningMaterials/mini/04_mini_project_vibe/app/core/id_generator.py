"""시간 기반 17자리 문자열 ID를 안전하게 생성합니다."""

from datetime import datetime
from threading import Lock
from zoneinfo import ZoneInfo


SEOUL = ZoneInfo("Asia/Seoul")
_id_lock = Lock()
_last_millisecond = 0


def generate_time_id() -> str:
    """동일 프로세스에서 같은 밀리초 ID가 중복되지 않도록 생성합니다."""

    global _last_millisecond

    with _id_lock:
        current_millisecond = int(datetime.now(SEOUL).timestamp() * 1000)
        next_millisecond = max(current_millisecond, _last_millisecond + 1)
        _last_millisecond = next_millisecond

    value = datetime.fromtimestamp(next_millisecond / 1000, SEOUL)
    return value.strftime("%Y%m%d%H%M%S%f")[:17]
