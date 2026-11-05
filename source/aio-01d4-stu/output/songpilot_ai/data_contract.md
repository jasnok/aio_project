# SongPilot AI 데이터 계약 초안

상태: **설계 단계**. Python 파일은 데이터 구조 검증용이며 앱·LLM 호출·검수 엔진·워크플로우를 구현한 것이 아니다. JSON 예시는 지자체 폭염 예방 캠페인이라는 **가상 업무 사례**를 수작업으로 작성했다. 실제 기관 도입, LLM 실행, 담당자 승인 기록은 없다.

## 파일과 실행

- `models.py`: Pydantic v2 계약, 필수 필드·엄격한 타입·추가 필드 금지·revision/승인 일관성 검사.
- `package.schema.json`: 모델에서 생성한 JSON Schema. 다른 도구와의 구조 전달용.
- `example_package.json`: 가사와 Style Prompt를 분리한 미승인 예시. `design_example`, `draft`, 검수 `not_run`을 명시한다.

Pydantic v2가 설치된 환경에서 `python models.py`를 실행하면 JSON Schema를 생성하고 예시 구조 및 JSON 직렬화 왕복을 검사한다. 이 실행은 패키지 안의 검수 기록을 변경하거나 LLM 검수를 수행하지 않는다.

## 주요 계약

| 구역 | 역할 |
|---|---|
| request | 목적·대상·채널·목표 길이·언어·톤·필수 메시지/문구·금지어·표현 지침 |
| plan | 기획 요약·콘셉트·구성·전달할 필수 메시지 id |
| lyrics / style | 한국어 가사와 영어 음악 스타일 지시를 별도 필드로 전달 |
| review | 현재 revision의 항목별 결과·근거·설명, 실제 길이 검증 여부 |
| approval | 담당자·시각·승인 revision을 포함한 패키지 승인 상태 |
| history / errors | 노드별 실행 상태·이유와 오류 원인·재시도 가능 여부 |

`required_phrases`는 가사에 **원문이 정확히 포함**되어야 하는 문구다. `required_messages`는 표현이 달라도 **의미를 전달**해야 하는 요구사항이며 id별 근거 구절과 별도 의미 검수가 필요하다. 둘 중 최소 한 항목을 입력해야 한다. 통과한 메시지 검수의 `evidence`에는 가사에 실제 존재하는 연속된 구절만 넣는다. 이 검사는 인용 근거가 존재하는지 확인할 뿐 의미 전달 여부를 판정하지 않는다. 입력의 필수 문구에 금지어가 들어 있으면 임의로 수정하지 않고 사용자 확인으로 보낸다.

## 상태와 승인

`draft` → `running` → `awaiting_approval` → `approved`가 정상 경로다. 누락·의미 불확실·재시도 소진은 `needs_input`, 복구할 수 없는 실행 오류는 `failed`로 분기할 예정이다. `revision_attempts`는 콘텐츠 수정 횟수이며 최대 2회다. 네트워크 오류 재시도는 별도 정책으로 설계해야 한다.

승인 단계에는 기획·가사·스타일·현재 revision 검수 결과가 필요하다. 형식, 필수 문구, 금지어, 표현 지침 및 각 메시지 검수에 근거와 `pass` 기록이 있어야 한다. `schema_format`, `required_phrases`, `forbidden_terms`는 `deterministic`, `expression_guidelines`와 `message:*`는 `semantic` 또는 `human`으로 종류를 고정한다. 필수 검수를 `estimate`로 바꾸어 승인 게이트를 우회할 수 없다. 길이 추정은 실제 길이 확인과 다르므로 별도 항목으로 분리한다. `duration_verified`는 MVP에서 항상 `false`다. 승인 후 내용을 바꾸면 revision을 올리고 검수·승인을 초기화해야 한다.

Pydantic의 교차 필드 검증은 JSON Schema만으로 모두 재현되지 않는다. 특히 승인 게이트는 `models.py`를 통한 로드와 서버 측 상태 전이 검증이 필요하다. 기록된 `pass`의 진실성이나 승인자의 권한은 이 계약으로 증명되지 않는다. 저장 파일을 불러올 때는 승인 정보를 신뢰하지 않고 원본 실행 이력과 대조하거나 재승인해야 한다. 승인 대상은 제작 패키지이며, 외부 도구에서 생성된 음원과 게시·방송에는 별도 담당자 검토가 필요하다.

## 실제 확인한 범위

JSON Schema 생성, 수작업 예시의 Pydantic 구조 검증, JSON 직렬화·역직렬화 왕복을 확인했다. `verify_contract.py`에는 데이터 계약용 합성 정상 사례 3개와 타입·중복 id·입력 충돌·승인 우회·가사에 없는 근거·수정 상한 등 거부 사례 19개가 있다. 합성 승인 데이터는 메모리에서만 사용하며 실제 승인 결과물로 저장하지 않는다. 실제 LLM 결과, 필수 메시지 의미 검수, 실패 분기·재시도, Streamlit UI, 승인 처리, Markdown 저장/불러오기 및 외부 음원 생성은 미구현이다.
