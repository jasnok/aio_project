# 공통 작업 지침

## 대화 및 출력 규칙
- 코드 변경 제안 시 전체 git diff나 긴 코드 블록을 터미널에 직접 모두 출력하지 마세요.
- 변경된 파일명과 핵심 요약만 간단히 보여주고, 사용자가 요청하거나 확인할 때만 자세한 내용을 표시하세요.

## 모든 작업은 다음과 같은 식으로
<!-- ## 모든 소스 검색은 uv tool graphify 이용 -->
- 생성된 소스의 모든 기본 인터페이스 언어는 영어로 한다.
- 파이썬은 무조건 uv 사용
- 앞으로 생성하는 모든 문서는 기본적으로 한글로 작성한다.
- 문서는 기본적으로 영문대문자와 '-'로 만들고 확장자는 .md 로 한다
- 마크다운 문서에서 다이어그램은 mermaid 문법을 사용한다.
- 어떤 일을 하게 되면 우선 실행계획부터 세우는데 VIBE-WORK/{YYMMDD}/{내용}-IMP-PLAN.md 로 생성 (한글)
    - 단계 별로 작성
    - 각 단계의 항목은 체크리스트로
    - 작업을 마치게 되면 해당 항목들은 체크
    - 작업을 마치면 VIBE-WORK/{YYMMDD}/{내용}-PHASE00.md 와 같이 해당 단계별 작성
<!-- - uv tool 이용 graphify로 update (외부 GEMINI 환경변수 이용) : uv tool 이용해서 graphify를 업데이트한다. 외부 GEMINI 환경변수 (GEMINI_API_KEY, GEMINI_MODEL)를 이용하여 업데이트한다. -->
- git commit (필요한 한줄짜리 한글 코멘트) 및 push
## Git 저장 위치
- 사용자 요청에 따라 외부 서버에는 push하지 않는다.
- 이 프로젝트에서 push할 때는 `git push /mnt/c/aio-01d4-stu/Last3Mon/66/turl/.local-git/turl.git main`을 사용한다.
