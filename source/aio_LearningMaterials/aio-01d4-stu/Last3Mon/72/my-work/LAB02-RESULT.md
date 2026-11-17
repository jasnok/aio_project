# Lab 02 결과 · 2026-10-26

작업 위치: C:\aio-01d4-stu\Last3Mon\72 (WSL: /mnt/c/aio-01d4-stu/Last3Mon/72).

## 최종 결과
- 예제1: 규칙 우선 분류, 해당 앞 네 케이스 통과.
- 예제2: lab02 9/9, 기존 lab01 4/4.
- 예제3: 캐시 사용 p50 0.12초, 미사용 2.29초; hits 4/misses 1.
- 과제1: 최종 반복 15/15; LLM 1회 FAQ VPN p50 1.04초.
- 과제2: 최종 6/6; FAQ 번호 캐시 p50 0.18초, LLM 0회.
- 최종 회귀: lab02 9/9, lab01 4/4, challenge 15/15.
- 캐시 우회 추가 계약 검사 통과.

## 실행 보고서
- 과제1: runs/lab02-challenge-20261026-123022.json
- 과제2: runs/lab02-challenge2-20261026-123057.json
- 예제 회귀: runs/lab02-20261026-123033.json
- 기존 회귀: runs/lab01-20261026-123037.json
- FAQ cache bench: runs/bench-my-helpdesk-20261026-123058.json
- 캐시 우회: runs/lab02-cache-contract.json

단계별 원본 출력과 실패 기록은 runs/lab02-*.txt, 설명·성능·손실은 PERF.md, 작업 요청은 PROMPTS.md에 보관했다.

## 재현
현재 서버에는 최종 helpdesk.json이 게시되어 있다.

```bash
cd /mnt/c/aio-01d4-stu/Last3Mon/72
uv run tools/flow.py check my-work/helpdesk.json
uv run tools/flow.py test cases/lab02-challenge2.json -v
uv run tools/flow.py test cases/lab02-challenge.json -v --repeat 3
uv run tools/flow.py test cases/lab02.json -v
uv run tools/flow.py test cases/lab01.json -v
```

생성기는 `uv run --no-project python my-work/build_lab02.py 4`로 최종 JSON을 재생성한다. 1/2/3은 학습 단계로 되돌아가므로 재게시할 때 주의한다. 생성만으로 서버가 바뀌지는 않는다.
