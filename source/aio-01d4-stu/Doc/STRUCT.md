# 프로젝트 구조 및 학습 가이드 (Project Structure & Curriculum)

본 문서는 AI 워크플로우 및 멀티 에이전트 오케스트레이션 교육 과정 수강생 저장소(`aio-01d4-stu`)의 전체 구조, 학습 커리큘럼, 실습 환경을 종합적으로 정리한 가이드입니다.

---

## 1. 프로젝트 개요 (Overview)

- **과정명**: 노코드 멀티 에이전트 워크플로우 설계 및 운영
- **저장소 목적**: AI 워크플로우 개념 학습, 노코드(n8n) 및 경량 코드 엔진(`miniflow`)을 활용한 업무 자동화 실습 및 결과물 관리
- **주요 기술 스택**:
  - **운영체제**: Windows 11 WSL (Ubuntu)
  - **노코드 플랫폼**: n8n (Docker Compose 기반 로컬 구동)
  - **자체 실습 엔진**: Python 기반 `miniflow` (패키지 관리: `uv`, 테스트: `pytest`)
  - **LLM 제공자**: OpenAI API (`gpt-4.1-mini`), 로컬 Ollama (`gemma3:4b` / `gemma3:1b` 대체 경로)

---

## 2. 전체 디렉토리 구조 (Directory Tree)

```text
aio-01d4-stu/
├── Doc/                            # 교육과정 전체 문서 및 가이드
│   ├── AIO-CURRICULUM-DAILY.csv    # 1일차~120일차 일자별 전체 커리큘럼 명세
│   └── STRUCT.md                   # [본 문서] 프로젝트 구조 및 전체 학습 가이드
│
├── Lecture/                        # 이론 강의 자료 및 일자별 강의 가이드
│   ├── 64/                         # 64일차: AI 워크플로우 개념 및 구성요소
│   │   ├── 00-DAY64-PREP.md        # 실습 전 준비 가이드
│   │   ├── 00-DAY64-OVERVIEW.md    # 강의 슬라이드/개요 마크다운
│   │   ├── 01-STAGE1-AI-WORKFLOW-CONCEPT.md  # 1단계: 개념/DAG/아키텍처
│   │   ├── 02-STAGE2-LLM-TOOL-MEMORY.md      # 2단계: LLM, Tool, Memory 상호작용
│   │   ├── 03-STAGE3-AUTOMATION-SCENARIO.md  # 3단계: 자동화 시나리오 분석
│   │   ├── 04-QUIZ-AND-WRAPUP.md             # 퀴즈 및 정리
│   │   └── README.md               # 64일차 강의 목차 및 시간표
│   ├── 65/                         # 65일차: Trigger·Condition·Action & n8n 환경
│   │   ├── 00-DAY65-PREP.md        # 65일차 준비 가이드
│   │   ├── 00-DAY65-OVERVIEW.md    # 강의 개요 마크다운
│   │   ├── 01-STAGE1-TRIGGER-CONDITION-ACTION.md # 1단계: TCA 패턴
│   │   ├── 02-STAGE2-N8N-ENVIRONMENT.md          # 2단계: n8n 노드 및 화면
│   │   └── 03-STAGE3-SAMPLE-AI-WORKFLOW.md       # 3단계: 샘플 워크플로우 분석
│   ├── 66/                         # 66일차: 단일 업무 자동화 워크플로우 구현
│   │   ├── 00-DAY66-PREP.md        # 66일차 준비 가이드
│   │   ├── 00-DAY66-OVERVIEW.md    # 강의 개요 마크다운
│   │   ├── 01-STAGE1-DESIGN-AND-DATA-FLOW.md # 1단계: 데이터 흐름 설계
│   │   ├── 02-STAGE2-PARSE-AND-TRANSFORM.md  # 2단계: 파싱 및 데이터 변환
│   │   ├── 03-STAGE3-LOOP-PARALLEL-AND-FINISH.md # 3단계: 루프/병렬/완성
│   │   └── README.md               # 66일차 강의 목차 및 시간표
│   └── vibe-coding-cli-advantages.pdf # 보조 학습 자료
│
├── Last3Mon/                       # 실습 코드, n8n 환경 및 과제 수행 디렉토리
│   ├── .env                        # LLM API 키 및 환경 변수 (OpenAI 등)
│   ├── .env.example                # 환경 변수 템플릿
│   │
│   ├── 64/                         # 64일차 실습: LLM, Tool, Memory 기초
│   │   ├── SETUP-WSL-LLM.md        # WSL 및 LLM 환경 설정
│   │   ├── LAB-01-FIRST-WORKFLOW.md        # Lab 1: 첫 워크플로우 실행
│   │   ├── LAB-02-LLM-TOOL-MEMORY.md       # Lab 2: Tool 및 Memory 연결
│   │   ├── LAB-03-SCENARIO-ANALYSIS.md     # Lab 3: 시나리오 분석 및 설계
│   │   ├── templates/              # 업무 시나리오 분석 템플릿
│   │   ├── my-work/                # 수강생 개인 실습 결과물 저장소
│   │   └── workflow-lab/           # miniflow v1 엔진 (Python 패키지)
│   │
│   ├── 65/                         # 65일차 실습: TCA 및 n8n 시작
│   │   ├── SETUP-N8N.md            # Docker 기반 n8n 구동 및 키 등록
│   │   ├── LAB-01-CONDITION-IN-MINIFLOW.md # Lab 1: miniflow 분기(Condition/Switch)
│   │   ├── LAB-02A-FIRST-WORKFLOW-IN-BROWSER.md # Lab 2A: 브라우저 n8n 기본 실습
│   │   ├── LAB-02-N8N-FIRST-WORKFLOWS.md   # Lab 2: Webhook/IF/Switch 워크플로우
│   │   ├── LAB-03-AI-WORKFLOW-FAILOVER.md  # Lab 3: AI 워크플로우 및 Fallback 처리
│   │   ├── templates/              # TCA 설계 템플릿
│   │   ├── n8n/                    # n8n Docker compose 환경 & 워크플로우 JSON
│   │   └── workflow-lab/           # miniflow v2 (Condition/Switch 확장)
│   │
│   └── 66/                         # 66일차 실습: 회의록 자동화 (Parse/Loop/Merge)
│       ├── LAB-01-DESIGN-DATA-FLOW.md      # Lab 1: 입출력 및 데이터 흐름 설계
│       ├── LAB-02-BUILD-PARSE-TRANSFORM.md # Lab 2: LLM JSON 파싱 및 변환
│       ├── LAB-03-BUILD-LOOP-PARALLEL.md   # Lab 3: 반복/병렬 제어 및 완성
│       ├── templates/              # 활동지 및 데이터 플로우 설계서
│       ├── n8n/                    # 회의록 액션 추출 n8n 워크플로우 및 테스트 JSON
│       └── workflow-lab/           # miniflow v3 (JSON 출력/액션 파싱 확장)
│
└── tmp/                            # 강의 및 실습 참고용 이미지 자료
    └── pdfs/                       # n8n UI, 비교 차트 등 스크린샷
```

---

## 3. 주요 디렉토리별 세부 설명

### 1) `Doc/` (문서 및 커리큘럼)
- **`AIO-CURRICULUM-DAILY.csv`**: 전체 과정(1일~120일)의 일자별 진도표.
  - 1~24일차: 파이썬 백엔드(FastAPI), Git, DB(Supabase, Redis), Streamlit, 단위 프로젝트
  - 25~44일차: 프롬프트 엔지니어링, LangChain, Tool/MCP, RAG, LangGraph, 단위 프로젝트
  - 45~63일차: 멀티 에이전트 협업, Docker/배포, 가드레일/보안, AutoHealing 단위 프로젝트
  - **64~82일차 (현재 진행 구간)**: **노코드 멀티 에이전트 워크플로우 설계 및 운영** (n8n, miniflow, 엔터프라이즈 자동화)
  - 83~120일차: 최종 프로젝트
- **`STRUCT.md`**: 저장소 전반의 구조와 학습 진행 방식을 기술한 전체 가이드.

### 2) `Lecture/` (강의 교재)
- 일자별로 체계적으로 구성되어 있으며, PPT 대신 Markdown 기반 슬라이드와 설명문으로 작성되어 있습니다.
- **`00-DAYxx-PREP.md`**: 수업 전날 수강생이 준비해야 할 환경 및 배경 지식.
- **`00-DAYxx-OVERVIEW.md`**: 당일 학습할 전체 뼈대 및 핵심 개념 개요.
- **`01~03-STAGE*.md`**: 단계별 상세 이론 (개념, 데이터 흐름, 아키텍처, 실무 시나리오).
- **`04-QUIZ-AND-WRAPUP.md`**: 일일 학습 마무리, 퀴즈 및 다음 날 예고.

### 3) `Last3Mon/` (실습 및 결과물)
- 수강생이 직접 코드를 실행하고 워크플로우를 빌드하는 공간입니다.
- **`workflow-lab/` (miniflow)**:
  - 복잡한 프레임워크 없이 워크플로우의 내부 동작 원리(DAG, LLM 호출, Tool 바인딩, Memory 입출력, 분기/조건문, 상태 관리)를 투명하게 코드로 이해할 수 있도록 만든 실습용 엔진입니다.
  - `uv run miniflow run flows/<워크플로우.json>` 명령으로 실행하며, 실행 기록이 `runs/`에 JSON 형태로 남습니다.
- **`n8n/`**:
  - 실제 비즈니스 환경에서 사용하는 오픈소스 노코드 자동화 플랫폼입니다.
  - `docker compose`로 실행되며, 웹 브라우저(`http://localhost:5678`)에서 노드를 드래그 앤 드롭하여 트리거(Webhook/Manual), AI 노드(OpenAI), 분기(IF/Switch), 데이터 변환(Edit Fields/Code), 병렬/반복(Split/Merge)을 구성합니다.
- **`templates/` & `my-work/`**:
  - 시나리오 분석서, TCA 설계서, 활동지 템플릿이 제공되며 수강생의 과제 결과물을 `my-work/`에 보관합니다.

---

## 4. 학습 단계별 세부 내용 (Day 64 ~ Day 66)

| 일차 | 핵심 주제 | miniflow 실습 내용 | n8n 실습 내용 |
| :--- | :--- | :--- | :--- |
| **Day 64** | **AI 워크플로우 기초 & 아키텍처**<br>- LLM, Tool, Memory 연결<br>- 업무 자동화 시나리오 분석 | `01-llm-only.json`<br>`02-llm-tool.json`<br>`03-save-profile.json`<br>`04-recommend-with-memory.json`<br>`05-tech-support-ticket.json` | - 워크플로우 개념 및 DAG 구조 이해<br>- 시나리오 분석서 작성 실습 |
| **Day 65** | **Trigger·Condition·Action (TCA)**<br>- 조건 분기와 스위치<br>- n8n 환경 셋업 & Failover | `06-request-with-condition.json`<br>`07-route-by-category.json` | `01-condition-basics.json`<br>`02-webhook-router.json`<br>`03-ai-request-flow.json`<br>(플랫폼 전환 및 Failover) |
| **Day 66** | **단일 업무 자동화 구현**<br>- 데이터 흐름(Data Flow)<br>- JSON 파싱, 반복, 병렬 처리 | `08-meeting-actions.json` | `lab02-example1-parse-practice.json`<br>`lab02-example2-meeting-part1.json`<br>`lab03-examples-loop-merge-practice.json`<br>`01-meeting-actions-solution.json`<br>(회의록 → 액션 아이템 추출/요약) |

---

## 5. 실습 환경 실행 가이드 (Quick Start)

### 1) 환경 변수 설정
`Last3Mon/.env` 파일에 API 키가 설정되어 있어야 합니다:
```bash
cd Last3Mon
cp .env.example .env  # 필요시 복사 후 OPENAI_API_KEY 입력
```

### 2) miniflow 실행 및 테스트
각 일차의 `workflow-lab` 디렉토리에서 수행:
```bash
cd Last3Mon/66/workflow-lab
uv sync
uv run pytest -q        # 엔진 테스트 통과 확인
uv run miniflow check   # LLM 연결 상태 점검
uv run miniflow run flows/08-meeting-actions.json  # 워크플로우 실행
```

### 3) n8n 구동
```bash
cd Last3Mon/65/n8n
docker compose up -d    # n8n 및 로컬 Ollama 백그라운드 구동
./register-credentials.sh # .env의 OpenAI 키를 n8n Credential로 등록
```
- 브라우저 접속: `http://localhost:5678`

---

## 6. 학습 시 주의사항 및 팁

1. **코드(`miniflow`)와 노코드(`n8n`)의 상호 보완**:
   - `miniflow`를 통해 데이터가 노드 간에 어떻게 전달되고 JSON으로 직렬화되는지 근본 원리를 이해합니다.
   - 원리를 이해한 후 `n8n`을 통해 시각적으로 트리거, 조건 분기, 병렬 합치기를 구현하여 실무 생산성을 체득합니다.
2. **에러 핸들링 및 Fallback**:
   - OpenAI API 키 만료나 네트워크 에러 시 로컬 Ollama로 안전하게 Fallback(우회)하는 아키텍처가 구축되어 있습니다.
3. **결과물 보관**:
   - 과제 및 실습 결과물은 일자별 `my-work/` 폴더에 마크다운 및 JSON 파일로 저장하여 관리합니다.
