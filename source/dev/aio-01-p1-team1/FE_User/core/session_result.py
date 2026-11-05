"""한 사용자 세션에서 성공한 조회 결과 한 개만 잠시 재사용합니다."""
import time


def session_result(state, key, identity, load, ttl=60):
    cached = state.get(key)
    if cached and cached['identity'] == identity and time.monotonic() < cached['expires']:
        return cached['value']
    # 실패 결과나 오래된 결과는 보관하지 않습니다. 예외는 호출 화면이 안내합니다.
    state.pop(key, None)
    value = load()
    state[key] = {'identity': identity, 'expires': time.monotonic() + ttl, 'value': value}
    return value
