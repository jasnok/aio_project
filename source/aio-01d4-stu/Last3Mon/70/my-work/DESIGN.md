# 재사용 설계서 · 공지 키트와 규칙 검사 모듈

- 이름:
- 사용한 CLI 에이전트: codex
- 이 파일을 `my-work/DESIGN.md`로 복사해 채웁니다.

## 1. 복사본 비교 (Lab 01 예제 1)

| 노드 | 세 파일에서 같은가 | 다른 것 (점검 · 보안 · 교육) | 어디로 (모듈 · 설정 표 · 그대로) |
| --- | --- | --- | --- |
| Notice webhook | 방식은 같고 경로만 다름 | 모두 POST, responseNode. 경로는 `sample-maintenance` · `sample-security` · `sample-training` | 그대로: 통합 시 `my-notice-kit` 하나로 받고 본문의 `kind`로 종류 선택 |
| Has facts? | 같음 | 모두 `body.facts`가 비어 있지 않은지 검사 | 그대로: 공통 입력 검사 (통합 시 `kind` 필수 검사 추가) |
| Reject empty | 같음 | 모두 HTTP 400, `{"error":"facts are required"}` | 그대로: 공통 오류 응답 |
| Writer agent | 공통 작성 방식은 같고 종류별 지시가 다름 | 머리말: `[점검 안내]` · `[보안 안내]` · `[교육 안내]`. 점검: 사용 불가 대상과 작업 후 조치. 보안: 해야 할 일·금지 행동, 비밀번호 요구 금지, 필수 문장 `IT팀은 절대 비밀번호를 묻지 않습니다.`. 교육: 참석 대상·일시·장소·신청 방법, 필수 문장 `신청은 IT 포털에서 할 수 있습니다.` | 설정 표: 머리말·필수 문장·주의. 그대로: 사실만 사용, 제목 뒤 짧은 3~6줄, 날짜·시간 원문 유지, 없는 약속·보상·사람·연락처 추가 금지라는 공통 프롬프트 |
| OpenAI chat model | 같음 | 모두 `gpt-4.1-mini`, temperature 0, 동일 Credential `openAiCourse0001` | 그대로: 공통 모델 연결 |
| Build draft | 같음 | 모두 `output`을 문자열로 바꾸고 앞뒤 공백·코드 펜스 제거 → `draft` | 그대로: 공통 초안 정리 |
| Rule checks | 검사 로직은 같고 설정값만 다름 | 최대 길이: 600 · 500 · 800. 필수 문장 목록: 빈 목록 · 보안 문장 1개 · 교육 문장 1개. 모두 날짜·시간 누락, 휴대전화·메일, 길이 초과, 필수 문장 누락 검사 → `passed`, `codes`, `issues` | 모듈: 공통 검사 로직을 규칙 검사 모듈로 추출. 설정 표: `max_length`, `required_phrases`를 두고 호출 시 전달 |
| Build result | 결과 구조·판정은 같고 kind만 다름 | `kind`: `maintenance` · `security` · `training`. 모두 통과 시 `route="게시 가능"`, `published=true`, 실패 시 `route="담당자 확인"`, `published=false`. `notice`는 초안, `codes`는 검사 코드 | 그대로: 공통 결과 조립. `kind`는 선택한 종류 값을 사용 |
| Send result | 같음 | 모두 현재 JSON을 Respond to Webhook으로 응답 | 그대로: 공통 JSON 응답 |

입력은 세 파일 모두 `body.facts`(필수), `body.request`(선택, 없거나 빈 값이면 `공지`)다. 정상 흐름은 `Notice webhook → Has facts? → Writer agent → Build draft → Rule checks → Build result → Send result`이며, facts가 비면 `Reject empty`로 간다. OpenAI 모델은 Writer agent에 연결된다. 결과는 모두 `{kind, route, published, notice, codes}`이며, 실제 게시 노드 없이 검사 통과 여부를 `published`로 표시한다.

- 보안 공지의 규칙을 하나 고쳐야 한다면, 지금은 몇 곳을 고쳐야 하나?
  - 보안 필수 문장을 바꾸려면 `notice-security.json`의 `Writer agent` 지시와 `Rule checks` 설정, **노드 기준 2곳**을 고쳐야 한다. 현재 `Rule checks` 안에서도 같은 설정 객체를 6회 반복하므로 문장 값은 해당 노드 안의 6개 위치에 중복되어 있다.
  - 개인정보 검출처럼 세 종류에 공통인 검사 규칙을 바꾸려면 세 파일의 `Rule checks`, **3곳**을 고쳐야 한다. 설정 표와 검사 모듈로 추출하면 각각 한 곳에서 관리할 수 있다.

## 2. 설정 표 (Lab 01 예제 2 · 과제)

| kind | 머리말 | 최대 길이 | 꼭 넣을 문장 | 주의 |
| --- | --- | --- | --- | --- |
| maintenance |  |  |  |  |
| security |  |  |  |  |
| training |  |  |  |  |
| (새 종류) |  |  |  |  |

- 새 종류를 더할 때 고친 노드:

## 3. 모듈 계약 (Lab 02)

| 모듈 | id | 입력 (이름 · 종류) | 결과 | 쓰는 곳 |
| --- | --- | --- | --- | --- |
| 규칙 검사 |  |  |  |  |

## 4. 바꿀 때 (Lab 03)

| 바꾼 것 | 하위 호환인가 | 같은 id · 새 id | 다시 돌린 테스트 | 결과 |
| --- | --- | --- | --- | --- |
| 바깥 링크 검사 (`allowed_domains`) |  |  |  |  |
| 심각도 (`blocking` · `warnings`) |  |  |  |  |

## 5. 영향 표 (Lab 03 과제)

| 모듈 · 버전 | 쓰는 워크플로우 | 그 워크플로우의 테스트 |
| --- | --- | --- |
|  |  |  |
