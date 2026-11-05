# 성능 · 안정성 보고서 · IT 헬프데스크

- 이름:
- 사용한 CLI 에이전트: codex / claude / agy
- 이 파일을 `my-work/PERF.md`로 복사해 채웁니다.

## 1. 기준 재기 (Lab 01)

`uv run tools/flow.py bench base-helpdesk requests/<요청>.json -n 5`

| 요청 | p50 | p95 | max | 첫 호출 | 실패 |
| --- | --- | --- | --- | --- | --- |
| `faq-vpn` |  |  |  |  |  |
| `ticket-own` |  |  |  |  |  |
| `off-topic` |  |  |  |  |  |

## 2. 단계별 시간 (Lab 01 · `timings`)

| 요청 | classify | data (faq · ticket) | answer | review | total | 가장 오래 걸린 단계 |
| --- | --- | --- | --- | --- | --- | --- |
| `faq-vpn` | 647 ms | 28 ms | 1313 ms | 1576 ms | 3583 ms | review |
| `ticket-own` | 871 ms | 25 ms | 905 ms | 1677 ms | 3489 ms | review |

- LLM을 부를 필요가 없었던 요청 · 단계는?

### 2-1. 질문 종류별 (Lab 01 예제 3)

| 질문 종류 | p50 | p95 | classify | data | answer | review | total | LLM 몫 (%) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FAQ (VPN) |  |  |  |  |  |  |  |  |
| 접수 번호 (T-1002) |  |  |  |  |  |  |  |  |
| IT 밖 (점심 메뉴) |  |  |  |  |  |  |  |  |

### 2-2. 시간 예산 (Lab 01 과제 2)

| `budget_ms` | `total_ms` | `llm_ms` | `over_budget` | `slowest_step` |
| --- | --- | --- | --- | --- |
| 60000 |  |  |  |  |
| 500 |  |  |  |  |
| (기본 3000) |  |  |  |  |

## 3. 한 가지씩 바꾸기 (Lab 02)

| 바꾼 것 (한 번에 하나) | `llm_calls` | p50 | p95 | 품질 테스트 (`lab01` · `lab02`) | 잃은 것 |
| --- | --- | --- | --- | --- | --- |
| 기준 | 3 | 3.08s | 3.45s | lab01 4/4 | 없음 |
| 규칙 먼저 | 2 | 2.50s | 2.60s | lab02 앞 네 케이스 통과 | 규칙 적용 범위 밖은 분류 필요 |
| 캐시 (같은 질문 두 번째) | 0 | 0.12s | 2.33s | lab02 9/9, lab01 4/4 | 최대 600초 오래된 FAQ 답 |
| 검토 → 검사 (과제 1) | 1 | 1.04s | 1.40s | challenge 15/15, lab02 9/9, lab01 4/4 | 뜻·근거를 재검토하는 LLM 제거 |
| FAQ 번호 캐시 (과제 2, 다른 말 질문) | 0 | 0.18s | 0.20s | challenge2 6/6, challenge 15/15, lab02 9/9, lab01 4/4 | 최초 질문에 맞춘 답 재사용: 질문별 세부 차이 손실 |

### 3-1. 캐시 적중률 (Lab 02 예제 3)

| 재기 | 첫 호출 | p50 | max | hits · misses |
| --- | --- | --- | --- | --- |
| 캐시 씀 | 2.33s | 0.12s | 2.33s | hits 4 · misses 1 |
| 캐시 안 씀 | 2.23s | 2.29s | 2.57s | 변화 없음 (4 · 1 유지) |

- 적중률 10% · 30%일 때 평균 어림: 캐시 0.12초·미사용 2.29초 기준 2.073초 / 1.639초. 동일 질문 5회 조회 적중률은 4/5=80%. no_cache 요청은 조회하지 않으므로 통계에 포함되지 않음.

## 4. 멈췄을 때 (Lab 03)

| 상황 | 고치기 전 (시간 · 결과) | 고친 뒤 (시간 · route) |
| --- | --- | --- |
| FAQ가 느림 (8초) |  |  |
| FAQ가 오류 (500) |  |  |
| LLM이 멈춤 (`llm down`) |  |  |
| 캐시에 있는 질문 + FAQ 오류 |  |  |
| 접수 API만 오류 · 접수 질문 (예제 3) |  |  |
| 접수 API만 오류 · VPN 질문 (예제 3) |  |  |
| FAQ 느림 · 다음 질문 (과제 2 차단기) |  |  |

## 5. 상태 점검 (Lab 03 과제)

| 상황 | `status` | `checks` | 걸린 시간 |
| --- | --- | --- | --- |
| 평소 |  |  |  |
| FAQ 오류 |  |  |  |
| FAQ 느림 |  |  |  |
| LLM 멈춤 |  |  |  |

## 6. 운영 관점 개선 제안 (3줄)

- 

## Lab 01 example 2 validation

- 2026-10-26: check passed; published my-helpdesk; lab01 tests passed 4/4.
- Report: runs/lab01-20261026-104243.json
- Timings above are workflow-internal milliseconds from single test requests, not benchmark percentiles.
- First FAQ request: total_ms=5861; external elapsed=9.3s. Second FAQ request: total_ms=3583; external elapsed=3.8s.


## Lab 02 실제 실행 결과 · 2026-10-26

- 작업 기준: Windows `C:/aio-01d4-stu/Last3Mon/72`, WSL에서는 `/mnt/c/aio-01d4-stu/Last3Mon/72`. 홈 저장소와 파일을 자동 동기화하지 않았다.
- 사용한 CLI 에이전트: Codex. 사용자 요청으로 직접 구현·게시·실행했다.
- reference의 검증된 예제 구조를 활용하고 캐시 우회·FAQ 캐시·검토 Code·시간 기록을 추가했다. 테스트와 tools, data-api, requests, reference는 변경하지 않았다.
- 예제1 앞 네 케이스 통과. 전체 8/9의 유일한 실패는 아직 미구현인 질문 캐시였다.
- 예제2: lab02 9/9, lab01 4/4.
- 과제1: 재검증 15/15. 캐시 없는 VPN bench p50 1.04s / p95 1.40s. 기준 p50 3.08s 대비 약 66% 감소.
- 과제2: 최종 6/6, 다른 말 FAQ cache_by=faq / 같은 말 cache_by=question / no_cache와 ticket cached=false.
- 추가 검사: 캐시 비운 뒤 no_cache와 ticket 요청 전후 entries/hits/misses 동일. reads/writes 모두 생략 확인.
- 최초 과제1 검증 14/15, 과제2 5/6 실패도 원본 보고서에 남겼다. 게시 직후 첫 응답에 직전 버전의 review 또는 cache_by 누락이 관찰되어 새 버전 응답을 확인한 뒤 재검증했다. 서버 내부 원인은 단정하지 않는다.
- 실제 경과 시간은 외부 flow.py 초 단위 측정이며 timings는 내부 ms이다. 워밍업·네트워크·모델 응답에 따라 변동한다. 2.5초는 이번 검증에서 통과한 값이며 보장 SLA가 아니다.
- Code 검토는 빈 답·한글·400자를 확인할 뿐 의미·근거 검증을 대체하지 못한다. 400자 자르기로 문장·핵심 정보가 손실될 가능성이 있다.
- 질문 캐시 5회 중 hits 4/misses 1=80%. no_cache bench 전후 통계 변화 없음. FAQ 캐시는 유사 질문 적중을 높이지만 최초 질문에 맞춘 답을 공유한다. 원문 변경 반영은 캐시 삭제 또는 ttl 600초 만료 후다.
- Lab 03 안정성·장애 주입 과제는 이번 범위가 아니며 미실행.

### 보고서와 원본 출력

- `runs/lab02-baseline-bench.txt`: p50 3.08s · p95 3.45s · max 3.45s · failures 0/5 · `runs/bench-my-helpdesk-20261026-122407.json`
- `runs/lab02-baseline-test.txt`: Passed 4/4 · `runs/lab01-20261026-122351.json`
- `runs/lab02-cache-bench.txt`: p50 0.12s · p95 2.33s · max 2.33s · failures 0/5 · `runs/bench-my-helpdesk-20261026-122712.json`
- `runs/lab02-cache-contract.txt`: PASS: no_cache and ticket skip both cache reads and writes
- `runs/lab02-faqcache-bench.txt`: p50 0.18s · p95 0.20s · max 0.20s · failures 0/5 · `runs/bench-my-helpdesk-20261026-123058.json`
- `runs/lab02-nocache-bench.txt`: p50 2.29s · p95 2.57s · max 2.57s · failures 0/5 · `runs/bench-my-helpdesk-20261026-122723.json`
- `runs/lab02-stage1-bench.txt`: p50 2.50s · p95 2.60s · max 2.60s · failures 0/5 · `runs/bench-my-helpdesk-20261026-122544.json`
- `runs/lab02-stage1-test.txt`: Passed 8/9 · `runs/lab02-20261026-122532.json`
- `runs/lab02-stage2-regression.txt`: Passed 4/4 · `runs/lab01-20261026-122709.json`
- `runs/lab02-stage2-test.txt`: Passed 9/9 · `runs/lab02-20261026-122702.json`
- `runs/lab02-stage3-bench.txt`: p50 1.04s · p95 1.40s · max 1.40s · failures 0/5 · `runs/bench-my-helpdesk-20261026-122846.json`
- `runs/lab02-stage3-challenge-confirm.txt`: Passed 15/15 · `runs/lab02-challenge-20261026-122922.json`
- `runs/lab02-stage3-challenge.txt`: Passed 14/15 · `runs/lab02-challenge-20261026-122826.json`
- `runs/lab02-stage3-regression.txt`: Passed 4/4 · `runs/lab01-20261026-122840.json`
- `runs/lab02-stage3-test.txt`: Passed 9/9 · `runs/lab02-20261026-122837.json`
- `runs/lab02-stage4-challenge1.txt`: Passed 15/15 · `runs/lab02-challenge-20261026-123022.json`
- `runs/lab02-stage4-challenge2-confirm.txt`: Passed 6/6 · `runs/lab02-challenge2-20261026-123057.json`
- `runs/lab02-stage4-challenge2.txt`: Passed 5/6 · `runs/lab02-challenge2-20261026-123005.json`
- `runs/lab02-stage4-regression.txt`: Passed 4/4 · `runs/lab01-20261026-123037.json`
- `runs/lab02-stage4-test.txt`: Passed 9/9 · `runs/lab02-20261026-123033.json`
