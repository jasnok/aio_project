# SongPilot AI 설계 패키지

2026-10-26 작성. **현재 단계는 설계이며 서비스 구현 완료가 아니다.**

지자체 시민안전 홍보팀의 폭염 예방 캠페인을 가상 업무 사례로 사용했다. 실제 기관 도입 사례·LLM 실행 결과·담당자 승인 이력을 만들지 않았다.

## 읽는 순서

1. `SongPilot_AI_프로젝트_기획서_1페이지.pdf`: A4 세로 1페이지 요약. 별도 `output/pdf/`에 저장되어 있으며 배포 ZIP에는 문서들과 함께 포함된다.
2. `01_프로젝트_기획서_원문.md`: 편집 가능한 기획 원문.
3. `02_MVP_설계서.md`: 현실성 검토 → 아키텍처 → 책임 분담 → 상태·워크플로우 → 데이터 → 검수·실패 → 저장·불러오기 → 단계별 구현 → 테스트 계획.
4. `workflow.mmd`: 워크플로우 Mermaid 원본. 같은 다이어그램이 설계서에도 포함된다.
5. `data_contract.md`, `models.py`, `package.schema.json`: 데이터 계약 설명·Pydantic v2 초안·JSON Schema.
6. `example_package.json`: 가사·Style Prompt를 분리한 미승인 설계 예시.
7. `verify_contract.py`: 데이터 계약 검증용 정상·거부 사례.
8. `build_pdf.py`: Windows 맑은 고딕과 ReportLab을 사용한 PDF 재생성 도구. MVP 앱 코드가 아니다.

## 이번에 실제 확인한 범위

- PDF는 A4(595.28 × 841.89 pt), 1페이지이며 11개 필수 텍스트 항목 추출 검사 통과.
- Poppler로 PDF를 PNG로 렌더링하고 한국어 글꼴·여백·잘림·배치를 시각 확인.
- Pydantic으로 JSON Schema 생성, 예시 구조 검증 및 JSON 직렬화 왕복 확인.
- 데이터 계약 검증 정상 3건·거부 19건 통과. 잘못된 타입, 중복 ID, 조건 충돌, 오래된 revision, 승인 우회, 가사에 없는 근거 등을 검사했다.

서비스·LLM 연동·의미 검수 엔진·LangGraph 실행·재시도 워크플로우·Streamlit UI·Markdown 저장/불러오기 서비스·승인 UI·음원 생성은 미구현이다. 설계서의 T01~T20은 향후 서비스 테스트 계획이며 이번 검증 22건과 다르다.

## 데이터 계약 검증 실행

Python과 Pydantic v2가 있는 환경에서 이 폴더를 기준으로 실행한다.

```powershell
python models.py
python verify_contract.py
```

예시 JSON은 `design_example`, `draft`, 검수 `not_run`, 승인 `pending`이다. 실제 길이 검증은 `duration_verified=false`로 유지한다. 예시의 채널·BPM·가사·표현 지침은 설계 설명을 위해 추가한 가정이며 사용자가 확정한 실제 업무 조건이 아니다.

## 범위 결정

단일 캠페인·트랙, LLM 공급자 하나, 기획·가사·스타일·검수 역할과 코드 규칙 검증을 사용한다. 콘텐츠 수정은 최초 생성 후 최대 2회이며 통신 재시도와 구별한다. 조건이 모호하거나 충돌하면 사용자 확인으로 보낸다. 승인 뒤 내용 변경 시 검수와 승인을 초기화한다. 패키지 승인과 실제 음원·게시·방송 승인은 별도다.

기본 스택은 Python + LangGraph + Pydantic + Streamlit + JSON + pytest다. 영속 승인 대기 복구는 별도 체크포인터를 포함하는 구현 단계에서 검증한다. RAG·Docker·여러 트랙은 핵심 기능 확인 후 검토한다.

## 자료 확인 상태

레퍼런스 [Wavenox Suno Command Maker](https://free.wavenox.com/tools/suno-command-maker/) URL을 PDF와 문서에 보존했다. 작성 시 접근 오류로 세부 기능은 확인하지 못했으며 기능 비교를 완료했다고 주장하지 않는다. 기술 설계 참고 자료는 설계서 끝의 공식 문서 링크에 기록했다.

기존 동명 PDF는 작업 폴더에서 확인되지 않아 제공받은 수정 방향으로 새로 작성했다. 기존 파일을 편집·검토한 것으로 설명하지 않는다.
