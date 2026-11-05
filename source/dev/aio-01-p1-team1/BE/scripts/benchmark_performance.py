"""공고 검색의 전후 비교. 생성·수정 없이 지정한 로컬 API만 읽습니다."""
import argparse
import json
import math
import statistics
import time
from pathlib import Path
from urllib.parse import urlencode, urlsplit

import httpx


def measure(client, path, samples, transform=lambda data: data):
    times = []
    for _ in range(samples):
        start = time.perf_counter()
        response = client.get(path)
        response.raise_for_status()
        items = transform(response.json()['data'])
        times.append((time.perf_counter() - start) * 1000)
    return {'samples': samples, 'median_ms': round(statistics.median(times), 2),
            'p95_ms': round(sorted(times)[math.ceil(samples * .95) - 1], 2),
            'response_bytes': len(response.content), 'result_count': len(items)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:18000')
    parser.add_argument('--samples', type=int, default=30)
    parser.add_argument('--query', default='특별대상')
    parser.add_argument('--mode', choices=['before', 'after'], required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--admin-fixture', help='로컬 검증용 관리자 정보 JSON. 값은 출력하지 않습니다.')
    args = parser.parse_args()
    if urlsplit(args.url).hostname not in ('127.0.0.1', 'localhost', '::1'):
        parser.error('Only local loopback API URLs are supported')
    if not 5 <= args.samples <= 100:
        parser.error('samples must be between 5 and 100')
    with httpx.Client(base_url=args.url, timeout=30) as client:
        client.get('/listings/getall').raise_for_status()  # 동일하게 한 번 예열합니다.
        if args.mode == 'before':
            result = measure(client, '/listings/getall', args.samples,
                             lambda rows: [r for r in rows if args.query in r['title']])
        else:
            result = measure(client, '/listings/location-candidates?' + urlencode({'query': args.query}), args.samples, lambda page: page['items'])
        report = {'mode': args.mode, 'query': args.query, 'search': result,
                  'scope': 'Local loopback API, warm persistent client; before full-list client filter, after first candidate page. Not a load test.'}
        if args.admin_fixture:
            credentials = json.loads(Path(args.admin_fixture).read_text())
            login = client.post('/admin/login', json={'username': credentials['username'], 'password': credentials['password']})
            login.raise_for_status()
            client.headers['Authorization'] = 'Bearer ' + login.json()['data']['access_token']
            report['ranking'] = measure(client, '/admin/favorites/ranking', args.samples)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
