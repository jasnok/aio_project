"""지도 전용 연결 재사용과 시설 조회의 동시 실행 수를 제한합니다."""
from concurrent.futures import ThreadPoolExecutor, wait
from threading import Lock, BoundedSemaphore

import httpx
from app.core.external_error import ExternalServiceError

_lock = Lock()
_client = None
_pool = None
_groups = BoundedSemaphore(6)


def get_location_client():
    global _client
    with _lock:
        if _client is None:
            _client = httpx.Client(limits=httpx.Limits(max_connections=3, max_keepalive_connections=3))
        return _client


def parallel_categories(load):
    global _pool
    if not _groups.acquire(timeout=10):
        raise ExternalServiceError('kakao', 'busy', '위치 검색 요청이 많습니다. 잠시 후 다시 시도해 주세요.', 503)
    try:
        with _lock:
            if _pool is None:
                _pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix='housing-location')
            pool = _pool
        # 결과 순서는 항상 지하철·마트·병원입니다. 한 항목 실패 시 성공 응답을 만들지 않습니다.
        futures = [pool.submit(load, category) for category in ('subway', 'mart', 'hospital')]
        try:
            return [future.result() for future in futures]
        finally:
            # 실패한 요청도 나머지 작업이 끝난 뒤 슬롯을 반납합니다.
            wait(futures)
    finally:
        _groups.release()


def close_location_runtime():
    global _client, _pool
    with _lock:
        pool = _pool
    if pool:
        pool.shutdown(wait=True, cancel_futures=True)
    with _lock:
        client = _client
        _pool = _client = None
    if client:
        client.close()
