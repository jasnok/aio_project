
## Lab 02 예제 1 · 계약 표 작성 요청

C:\aio-01d4-stu\Last3Mon\68\AGENTS.md를 먼저 읽어 주세요.

Lab 02 예제 1의 계약 표를 작성해 주세요.
agents/it-agent.json과 agents/meeting-agent.json의
웹훅, 입력 검사, 응답 관련 노드를 읽고
my-work/DESIGN.md 2절의 기존 표를 채워 주세요.

표에는 Agent, 맡는 업무, 웹훅, 입력의 필수·선택 여부,
결과 필드와 구조, 실패 시 HTTP 상태·응답을 기록하세요.

아래 실제 호출 결과와 파일 내용을 비교하세요.
호출로 확인된 사실과 파일에서 확인한 동작을 구분하고,
차이가 있으면 설명하세요.

워크플로우는 만들거나 수정하지 마세요.
DESIGN.md의 다른 절과 기존 내용을 유지하세요.
이 요청문은 my-work/PROMPTS.md 끝에 추가하세요.
push와 test는 실행하지 마세요.

실제 호출 결과:
[지금 받은 터미널 출력 전체를 여기에 붙여 넣기]

## assistant.json · Sticky Note 경고 정리 요청

AGENTS.md를 먼저 읽어 주세요.

my-work/assistant.json을 push할 때 다음 노드에서
nothing is connected into it 경고가 나옵니다.

- Input group
- Split group
- Dispatch group
- Collect group
- Exception group

각 노드의 type을 확인하세요.
n8n-nodes-base.stickyNote인 경우에만 해당 노드를 삭제하세요.
다른 type이면 삭제하지 말고 원인부터 설명하세요.

실행 노드, connections, 웹훅, 업무 분할·분배·응답 로직은 유지하세요.
tools/flow.py와 AGENTS.md, 기존 Agent 파일은 수정하지 마세요.

수정 후 아래 검사를 실행하세요.
uv run tools/flow.py check my-work/assistant.json

변경 사항과 검사 결과를 알려 주세요.
push와 test는 제가 직접 실행하겠습니다.
이 요청문은 my-work/PROMPTS.md 끝에 추가하세요.

## Lab 03 예제 1 · 입력 누락 분기 수정 요청

AGENTS.md를 먼저 읽어 주세요.

Lab 03 예제 1 테스트에서 5개 중 1개가 실패했습니다.

실패 케이스: 회의록 없는 회의 요청
보고서: runs/lab03-20261020-144651.json
실패 내용:
results.0.route = 담당자 연결 (expected 입력 필요)

나머지 IT 둘, 복합 요청, 기타만, 빈 요청은 통과했습니다.

먼저 아래 파일을 읽고 원인을 설명하세요.
- my-work/assistant.json
- runs/lab03-20261020-144651.json
- cases/lab03.json
- cases/lab02.json

입력 누락이 일반적인 담당자 연결로 처리되는 위치를 확인한 뒤,
기존 my-work/assistant.json을 수정하세요.

수정 조건:
1. Agent 호출 전에 원래 웹훅 요청 본문의 필수 입력을 검사하세요.
   - meeting: notes
   - it: user
   - 필드 없음, null, 공백뿐인 문자열을 누락으로 처리하세요.
2. 기존 missing 계산이 있으면 확인하고 활용하세요.
3. 누락 여부는 코드로 판단하고 LLM 지시문은 유지하세요.
4. 입력이 부족한 업무는 Agent를 호출하지 않고 다음 결과를 만드세요.
   - route: "입력 필요"
   - notes 누락 answer: "회의록 원문(notes)을 보내 주세요."
   - user 누락 answer: "요청한 사람(user)을 보내 주세요."
5. 해당 업무의 index, type, text, agent를 유지하고
   results와 count에도 포함하세요.
6. 다른 업무는 계속 처리하고 결과 순서를 유지하세요.
7. 현재 통과하는 네 케이스와 cases/lab02.json의 동작을 유지하세요.

테스트 파일, 기존 Agent 파일, tools/는 수정하지 마세요.
DESIGN.md 5절의 입력 누락 처리 내용을 갱신하고,
이 요청문을 my-work/PROMPTS.md 끝에 추가하세요.
실제 재검증 전에는 테스트를 통과했다고 기록하지 마세요.

수정 후 아래 검사를 실행하고 오류가 있으면 수정하세요.
uv run tools/flow.py check my-work/assistant.json

push와 test는 제가 직접 실행하겠습니다.
마지막에 원인, 변경 사항, check 결과를 알려 주세요.
