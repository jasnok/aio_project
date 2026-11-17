import json,re
from pathlib import Path
p=Path(__file__).parent;r=p.parent/'runs'
s=(p/'PERF.md').read_text()
s=s.replace('| 검토 → 검사 (과제 1) | 1 | 1.04s | 1.40s | lab02 9/9, lab01 4/4; challenge 보고서 참조 |','| 검토 → 검사 (과제 1) | 1 | 1.04s | 1.40s | challenge 15/15, lab02 9/9, lab01 4/4 |')
s=re.sub(r'\| FAQ 번호 캐시 \(과제 2, 다른 말 질문\) \|.*','| FAQ 번호 캐시 (과제 2, 다른 말 질문) | 0 | 0.18s | 0.20s | challenge2 6/6, challenge 15/15, lab02 9/9, lab01 4/4 | 최초 질문에 맞춘 답 재사용: 질문별 세부 차이 손실 |',s)
s+='''

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
'''
for f in sorted(r.glob('lab02-*.txt')):
 text=f.read_text()
 summaries=re.findall(r'Passed \d+/\d+|p50 .*|PASS:.*',text)
 reports=re.findall(r'^report: (.+)$',text,re.M)
 s+='\n- `runs/'+f.name+'`: '+(' / '.join(summaries) if summaries else '단계 실행 출력')+(' · '+', '.join('`'+v+'`' for v in reports) if reports else '')
(p/'PERF.md').write_text(s+'\n')
