r"""JSON 파일을 안전하게 읽는 예제입니다.

실행 위치:
    C:\aidev\01_python-git-foundation

실행 명령:
    python .\02_python-advanced\02_exception-debugging\03_read_json_safely.py

이 예제의 목표:
    1. JSON 파일을 읽습니다.
    2. 파일이 없을 때의 오류를 처리합니다.
    3. JSON 문법이 깨졌을 때의 오류를 처리합니다.
"""

import json
from pathlib import Path
from mypackage.file import read_json_safely

CURRENT_DIR = Path(__file__).parent



def main() -> None:
    for file_name in ["config.json", "missing.json", "broken_config.json"]:
        print()
        print("읽는 파일:", file_name)
        config = read_json_safely(file_name)
        print("읽은 결과:", config)


main()
