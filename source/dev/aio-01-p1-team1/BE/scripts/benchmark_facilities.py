"""시설 조회 전후 비교: 각 제공자가 40ms 걸리는 통제된 모의 실험입니다."""
import argparse
import json
import statistics
import subprocess
import sys
import time
import types
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'BE'))
from app.services import location_service
from app.core.location_runtime import close_location_runtime


def measure(module):
    times = []
    with patch.object(module, 'find_nearby_facilities', side_effect=lambda **kwargs: (time.sleep(.04) or [])) as provider:
        for _ in range(10):
            start = time.perf_counter()
            module.find_nearby_living_facilities(37.5, 127.0)
            times.append((time.perf_counter() - start) * 1000)
    return {'median_ms': round(statistics.median(times), 2), 'samples': 10, 'provider_calls': provider.call_count}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    old = types.ModuleType('baseline_location')
    text = subprocess.check_output(['git', 'show', f'{args.baseline}:BE/app/services/location_service.py'], cwd=root).decode('utf-8')
    exec(compile(text, 'baseline_location.py', 'exec'), old.__dict__)
    try:
        report = {'scope': 'Three independent mock providers with 40ms delay each, NOT live Kakao.',
                  'before': measure(old), 'after': measure(location_service)}
    finally:
        close_location_runtime()
    Path(args.output).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
