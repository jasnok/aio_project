"""실제 API 대신 모의 응답으로 화면 재실행의 호출 횟수를 비교합니다."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'FE_User'))


def source(path, baseline):
    if baseline:
        return subprocess.check_output(['git', 'show', f'{baseline}:{path}'], cwd=root).decode('utf-8')
    return (root / path).read_text(encoding='utf-8')


def count_calls(baseline):
    location = source('FE_User/views/location.py', baseline)
    if baseline:
        helpers = source('FE_User/core/location_search.py', baseline)
        location = location.replace('from core.location_search import find_matching_listings, listing_label', helpers)
    listing = {'id': 1, 'title': '가상 공고', 'housing_name': '가상 주택', 'detail_address': '검증용 가상 주소'}
    with patch('clients.listing_client.get_listings', return_value={'data': [listing]}), \
         patch('clients.listing_client.search_location_listings', return_value={'data': {'items': [listing]}}), \
         patch('clients.location_client.geocode_location', return_value={'data': {'latitude': 37.5, 'longitude': 127.0}}) as geo, \
         patch('clients.location_client.get_nearby_facilities', return_value={'data': {}}) as facilities:
        at = AppTest.from_string(location + '\nrender()\n').run()
        at.text_input[0].set_value('가상')
        next(x for x in at.button if x.label == '주변생활권 탐색').click().run()
        for _ in range(3):
            at.run()
        assert not at.exception, str(at.exception)
        result = {'geocode_calls': geo.call_count, 'facilities_calls': facilities.call_count}
    summaries = source('FE_User/views/chat_summaries.py', baseline)
    with patch('clients.chat_client.get_chat_summaries', return_value={'data': []}) as get:
        at = AppTest.from_string(summaries + '\nshow_saved_summaries()\n')
        at.session_state['user_id'] = 'fixture-owner'
        at.session_state['access_token'] = 'fake-test-token'
        for _ in range(4):
            at.run()
        assert not at.exception, str(at.exception)
        result['summary_calls'] = get.call_count
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    report = {'scope': 'Four identical screen runs, mocked API. Measures call counts, not real provider latency.',
              'before': count_calls(args.baseline), 'after': count_calls(None)}
    Path(args.output).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
