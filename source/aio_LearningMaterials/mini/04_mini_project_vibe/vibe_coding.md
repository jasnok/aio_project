# FastAPI 팀 프로젝트 바이브 코딩 단계별 가이드

## 1. 문서 목적

이 문서는 `pre_plan.md`와 `dev_plan.md`를 기반으로 AI 코딩 도구와 협업하여 FastAPI 팀 프로젝트를 단계적으로 구현하는 방법을 설명한다.

바이브 코딩은 자연어 요청으로 코드를 빠르게 작성하는 방식이지만, AI가 프로젝트 구조와 팀 규칙을 임의로 바꾸지 않도록 사람이 단계별로 범위와 완료 조건을 통제해야 한다.

이 가이드의 핵심 원칙은 다음과 같다.

```text
작은 범위 요청 → 변경 내용 확인 → 테스트 → 커밋 → 다음 단계
```

한 번에 전체 프로젝트를 생성하도록 요청하지 않는다. 각 기능을 Schema, Service, Router, Test, Integration 순서로 나누어 진행한다.

## 2. 프로젝트 기준

- 개발 기간: 3일
- 팀원: 5명
- Python: 3.12.7
- Framework: FastAPI
- Validation: Pydantic v2
- Database: Supabase PostgreSQL
- Test: pytest
- LLM: Gemini API
- Deployment: Render Web Service
- 협업: GitHub 개인 브랜치 및 Pull Request

목표 기능:

1. User CRUD
2. Post CRUD
3. Comment CRUD
4. Support CRUD
5. Gemini Chat API

## 3. 바이브 코딩 기본 원칙

### 3.1 AI가 하기 좋은 작업

- 기존 구조 분석
- 반복적인 Schema, Service, Router 작성
- 타입 힌트 작성
- 입력 검증 작성
- pytest 초안 작성
- SQL 초안 작성
- Swagger 설명 작성
- 오류 원인 분석
- 문서 작성
- Render 설정 초안 작성

### 3.2 사람이 반드시 결정할 작업

- 기능 담당자와 작업 범위
- 데이터베이스 테이블명과 컬럼명
- 기본키 타입과 외래키 정책
- 삭제 시 CASCADE 또는 RESTRICT 정책
- Service Role Key 사용 여부
- 공통 응답 형식
- 병합 대상 브랜치
- 운영 샘플 데이터 포함 여부
- Render 환경변수 등록
- PR 승인 및 최종 병합

### 3.3 AI에게 맡기면 안 되는 작업

- 실제 API 키 생성 또는 추측
- `.env` 실제 값 출력
- 운영 데이터 임의 생성 또는 삭제
- 팀원 파일 무단 수정
- `main` 브랜치 직접 push
- 승인 없는 DB 테이블 삭제
- 실패 원인을 확인하지 않은 대규모 재작성
- 테스트를 통과시키기 위한 검증 삭제
- 비밀번호 평문 저장

## 4. 작업 시작 전 준비

### 4.1 계획 문서 읽기

AI에게 첫 요청으로 다음 문서를 읽게 한다.

```text
pre_plan.md와 dev_plan.md를 모두 읽고 현재 프로젝트 구조와 비교해 주세요.
아직 파일을 수정하지 말고 다음만 보고해 주세요.

1. 현재 폴더 구조
2. 계획과 현재 코드의 차이
3. 이미 구현된 기능
4. 누락된 기능
5. 충돌 가능성이 있는 공통 파일
6. 필요한 작업 순서
7. 보안상 먼저 확인할 항목
```

사람이 확인할 내용:

- AI가 실제 프로젝트 구조를 올바르게 읽었는가?
- `schemas`와 `schemes`를 혼동하지 않았는가?
- 다른 팀원의 기능을 자신의 범위에 포함하지 않았는가?
- `.env` 내용을 출력하지 않았는가?
- 존재하지 않는 파일을 있다고 가정하지 않았는가?

### 4.2 Git 상태 확인

```powershell
git branch --show-current
git status --short
git remote -v
```

확인 기준:

- 개인 브랜치에서 작업 중인가?
- 다른 팀원의 미커밋 변경이 있는가?
- 계획 문서처럼 담당 기능과 무관한 파일이 변경되어 있는가?
- `.env`가 추적되고 있지 않은가?

### 4.3 Python 환경 확인

```powershell
python --version
python -m pip --version
```

예상 Python 버전:

```text
Python 3.12.7
```

가상환경이 없다면 생성한다.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4.4 비밀정보 확인

AI에게 다음 규칙을 명시한다.

```text
.env 파일은 열거나 내용을 출력하지 마세요.
키 값은 코드, 테스트, SQL, 문서, 로그에 작성하지 마세요.
.env.example에는 placeholder만 사용하세요.
```

`.gitignore` 필수 항목:

```gitignore
.env
.env.*
!.env.example
__pycache__/
*.pyc
.pytest_cache/
```

## 5. 바이브 코딩 요청 작성법

### 5.1 좋은 요청 구조

AI 요청에는 다음 7개 항목을 포함한다.

1. 역할
2. 현재 단계
3. 수정 가능 파일
4. 수정 금지 파일
5. 구현 요구사항
6. 검증 명령
7. 완료 보고 형식

예시:

```text
당신은 FastAPI 백엔드 개발자입니다.
현재 단계는 User Schema 구현입니다.

수정 가능 파일:
- app/schemas/user_schema.py
- tests/test_user_router.py 중 Schema 검증 테스트

수정 금지 파일:
- app/main.py
- 다른 기능의 Router, Service, Schema, SQL
- .env

요구사항:
- 이메일 필수 및 형식 검증
- 이메일 소문자 정규화
- 비밀번호 8~128자
- 이름 공백 입력 금지
- 응답 Schema에 password 제외
- Python 3.12.7 호환

작업 후 pytest를 실행하고 변경 파일과 결과를 보고하세요.
```

### 5.2 피해야 할 요청

```text
프로젝트 전체를 알아서 완성해 줘.
```

이 요청은 다음 문제를 만들 수 있다.

- 기존 파일 덮어쓰기
- 팀원 파일 수정
- 잘못된 새 구조 생성
- 환경변수 하드코딩
- 검증되지 않은 SQL 생성
- 테스트를 실행하지 않은 완료 보고

## 6. 전체 바이브 코딩 흐름

```text
1. 분석
2. 공통 규칙 확정
3. Supabase SQL 작성
4. Schema 구현
5. Service 구현
6. Router 구현
7. 단위 테스트
8. 실제 Supabase 통합 테스트
9. 개인 기능 리뷰
10. PR 생성
11. 팀 통합
12. 전체 회귀 테스트
13. Render 배포 준비
14. Render 배포
15. 운영 URL 검증
16. 문서와 최종 보고
```

각 단계가 완료되기 전에는 다음 단계로 넘어가지 않는다.

## 7. 단계 1 — 프로젝트 분석

### 7.1 AI 요청 예시

```text
현재 프로젝트를 읽기 전용으로 분석해 주세요.
아직 코드는 수정하지 마세요.

확인 항목:
- 실제 폴더 구조
- Python 파일 목록
- schemas 또는 schemes 사용 여부
- Router, Service, Schema 작성 방식
- 공통 API 응답
- Supabase Client 사용 방식
- pytest 작성 방식
- requirements.txt 버전
- .gitignore
- 실행 앱
- 담당 기능 구현에 필요한 파일

.env의 실제 값은 읽거나 출력하지 마세요.
```

### 7.2 예상 산출물

- 현재 구조 요약
- 기존 규칙 목록
- 계획과 다른 부분
- 생성 또는 수정할 파일 목록
- 위험 요소

### 7.3 사람의 검증

- 파일 경로가 실제로 존재하는가?
- AI가 `app/main.py` 수정 제한을 이해했는가?
- Product 예제 등 제거 대상과 담당 범위를 구분했는가?
- Git 작업트리의 사용자 변경을 존중하는가?

### 7.4 완료 조건

- 구현 전에 필요한 파일이 확정됨
- 공통 파일 수정 여부가 팀에 공유됨
- 담당 범위가 명확함

## 8. 단계 2 — 공통 규칙 확정

팀원 5명이 각각 코드를 만들기 전에 다음 내용을 합의한다.

### 8.1 필수 합의 항목

- 폴더명: `schemas`
- 파일명: `*_schema.py`, `*_service.py`, `*_router.py`
- ID 타입: `str`
- ID 형식: 17자리 시간 문자열 또는 팀 공통 방식
- 공통 응답: `success`, `message`, `data`
- 생성 상태 코드: 201
- 미존재 상태 코드: 404
- 중복 상태 코드: 409
- 입력 검증: 422
- 내부 오류: 500
- 시간 타입: `timestamptz`
- 시간대: Asia/Seoul 또는 DB UTC 저장 정책
- 병합 대상 브랜치: 예를 들어 `ykw`
- 공용 앱 수정 담당자

### 8.2 AI 요청 예시

```text
pre_plan.md와 dev_plan.md를 기준으로 팀 공통 코딩 규칙 체크리스트를 만들어 주세요.
코드는 수정하지 마세요.
ID, 상태 코드, 응답 형식, 파일명, 예외 클래스, 시간대, 테스트 방식의 충돌 가능성을 표시해 주세요.
```

### 8.3 완료 조건

- 모든 담당자가 동일한 ID와 외래키 타입을 사용함
- 공용 파일 담당자가 정해짐
- 각 개인 PR의 base 브랜치가 확정됨

## 9. 단계 3 — Supabase 데이터베이스 설계

### 9.1 실행 순서

```text
users → posts → comments → supports → trigger → index → sample data
```

### 9.2 SQL 작성 요청 예시

```text
현재 단계는 Supabase PostgreSQL SQL 작성입니다.
담당 기능은 User CRUD입니다.

sql/user.sql만 작성해 주세요.

조건:
- user_id text primary key
- YYYYMMDDHHMMSSmmm 형식 CHECK
- email NOT NULL, UNIQUE, 소문자
- password NOT NULL
- name NOT NULL
- created_at, updated_at timestamptz default now()
- updated_at 자동 갱신 trigger
- 개발용 샘플 데이터 10건
- 샘플 비밀번호는 평문 금지
- 반복 실행 가능한 형태
- DROP TABLE 금지
- Supabase SQL Editor 실행 가능

SQL은 실행하지 말고 파일만 작성하세요.
```

### 9.3 AI SQL 검토 요청

SQL을 바로 실행하지 않고 별도 검토 요청을 한다.

```text
sql/user.sql을 리뷰해 주세요.
수정하지 말고 다음 항목을 평가하세요.

- PostgreSQL 문법
- PK, UNIQUE, NOT NULL
- CHECK 정규식
- trigger 재실행 가능성
- sample data 중복 처리
- 평문 비밀번호 포함 여부
- 운영 환경 위험 SQL
```

### 9.4 사람이 Supabase에서 확인할 항목

- 테이블이 올바른 schema에 생성되는가?
- 컬럼 타입이 코드와 같은가?
- 외래키 컬럼 타입이 부모 테이블과 같은가?
- SQL Editor 오류가 없는가?
- 샘플 데이터가 예상 건수만 생성되는가?
- 샘플 비밀번호가 해시인가?
- `updated_at`이 UPDATE 후 변경되는가?

### 9.5 완료 조건

- 필요한 테이블과 제약조건 생성 완료
- 샘플 데이터 확인 완료
- SQL 파일과 실제 DB Schema 일치

## 10. 단계 4 — Pydantic Schema 구현

### 10.1 구현 순서

1. Create Schema
2. Update Schema
3. Public Response Schema
4. field validator
5. Swagger description 및 example
6. Schema 검증 테스트

### 10.2 User Schema 요청 예시

```text
app/schemas/user_schema.py만 구현해 주세요.

요구사항:
- UserCreate, UserUpdate, UserPublic
- email 필수, 최대 254자
- email 공백 제거 및 소문자 변환
- example@example.com 형식 검증
- password 8~128자
- name 공백 제외 1~100자
- user_id는 17자리 문자열
- created_at, updated_at은 datetime
- UserPublic에 password 금지
- Swagger에서 조건을 확인할 수 있는 description과 example
- 초보자용 짧은 docstring

Service와 Router는 수정하지 마세요.
```

### 10.3 검증 명령

```powershell
python -c "from app.schemas.user_schema import UserCreate; print(UserCreate(email='USER@EXAMPLE.COM', password='safe-password', name=' 테스트 '))"
```

잘못된 값도 확인한다.

```powershell
python -c "from app.schemas.user_schema import UserCreate; UserCreate(email='invalid', password='short', name=' ')"
```

### 10.4 사람이 확인할 항목

- 검증 메시지가 사용자에게 이해 가능한가?
- `password`가 공개 Schema에 없는가?
- Create와 Update 정책이 PUT 의미와 일치하는가?
- 필드 타입이 SQL과 같은가?

### 10.5 완료 조건

- 정상 Schema 생성 성공
- 잘못된 입력 검증 실패
- Swagger 설명 확인
- 공개 응답에 민감정보 없음

## 11. 단계 5 — Service 구현

### 11.1 구현 원칙

- HTTP 상태 코드를 사용하지 않는다.
- Supabase 쿼리를 Service에만 작성한다.
- DB 결과를 공개 Schema로 변환한다.
- 비밀번호를 해시한다.
- DB 내부 예외를 전용 예외로 감싼다.
- 존재하지 않는 데이터는 `None`을 반환한다.

### 11.2 AI 요청 예시

```text
app/services/user_service.py만 구현해 주세요.

필수 함수:
- _generate_user_id
- _hash_password
- _to_public
- _email_exists
- user_create
- user_get_all
- user_get
- user_update
- user_delete

조건:
- 공통 get_supabase() 재사용
- user_id는 서울 시간 기반 17자리 문자열
- 비밀번호는 PBKDF2-HMAC-SHA256, salt 16바이트, 600000회
- 조회 시 password 컬럼 제외
- 존재하지 않으면 None
- 중복 이메일은 DuplicateEmailError
- 기타 DB 오류는 UserServiceError
- DB 오류 문자열 외부 노출 금지
- 타입 힌트와 초보자용 docstring

Router와 SQL은 수정하지 마세요.
```

### 11.3 AI에게 추가로 요청할 중요 보완

```text
동일 밀리초 ID 충돌과 동시에 같은 이메일로 가입할 때의 DB unique violation을 검토해 주세요.
충돌이 일반 500으로 끝나지 않도록 안전한 최소 수정안을 제안하고 테스트를 추가하세요.
```

### 11.4 사람이 확인할 항목

- 비밀번호 원문이 insert 데이터에 들어가지 않는가?
- select 필드에 password가 없는가?
- `_email_exists`와 INSERT 사이 경쟁 조건을 이해하고 있는가?
- UserPublic 변환에서 타입 오류가 없는가?
- `user_id`가 DB에서 문자열로 반환되는가?

### 11.5 완료 조건

- Service 함수별 반환 타입 일치
- 비밀번호 해시 확인
- DB mock 테스트 통과
- 내부 오류 비노출

## 12. 단계 6 — Router 구현

### 12.1 AI 요청 예시

```text
app/routers/user_router.py만 구현해 주세요.

API:
- POST /users → 201
- GET /users → 200
- GET /users/{user_id} → 200 또는 404
- PUT /users/{user_id} → 200, 404 또는 409
- DELETE /users/{user_id} → 200 또는 404

조건:
- ApiResponse 사용
- Router는 Service만 호출
- Supabase 직접 호출 금지
- DuplicateEmailError는 409
- UserServiceError는 내부 정보를 숨긴 500
- password 응답 금지
- 타입 힌트와 짧은 docstring

다른 기능 파일과 app/main.py는 수정하지 마세요.
```

### 12.2 사람이 확인할 항목

- 경로가 단수와 복수 규칙에 맞는가?
- POST가 201인가?
- 404와 409가 구분되는가?
- 500에 DB 상세 메시지가 없는가?
- Router에 비즈니스 로직이 들어가지 않았는가?

### 12.3 완료 조건

- 5개 경로 등록
- Swagger에서 요청과 응답 확인
- Service 예외가 상태 코드로 변환됨

## 13. 단계 7 — pytest 단위 테스트

### 13.1 테스트 작성 요청 예시

```text
tests/test_user_router.py에 pytest를 작성해 주세요.
실제 Supabase를 호출하지 말고 monkeypatch를 사용하세요.

필수 테스트:
1. 생성 성공
2. 전체 조회 성공
3. 단일 조회 성공
4. 수정 성공
5. 삭제 성공
6. 없는 ID 조회 404
7. 없는 ID 수정 404
8. 없는 ID 삭제 404
9. 필수값 누락 422
10. 이메일 형식 오류 422
11. 짧은 비밀번호 422
12. 이메일 중복 409
13. 응답에 password 없음

테스트 간 데이터가 공유되지 않게 하고 실제 키를 사용하지 마세요.
```

### 13.2 실행

```powershell
python -m pytest tests/test_user_router.py -q
```

### 13.3 실패 시 AI 요청 방식

나쁜 요청:

```text
테스트 통과하게 고쳐 줘.
```

좋은 요청:

```text
다음 pytest 실패를 분석해 주세요.
먼저 원인을 설명하고, 테스트가 잘못된 것인지 구현이 잘못된 것인지 구분하세요.
검증 조건을 삭제하거나 약하게 만들지 마세요.
수정 범위는 User 기능 파일로 제한하세요.

[실패 로그]
```

### 13.4 완료 조건

- 담당 기능 전체 테스트 통과
- 실제 외부 서비스 호출 없음
- 민감정보 테스트 데이터 없음

## 14. 단계 8 — 실제 Supabase 통합 테스트

### 14.1 테스트 원칙

- 개발용 Supabase만 사용한다.
- 고유한 테스트 이메일을 사용한다.
- 생성한 ID를 기록한다.
- 성공과 실패에 관계없이 `finally`에서 삭제한다.
- 기존 운영 데이터를 수정하거나 삭제하지 않는다.
- 키 값을 출력하지 않는다.

### 14.2 AI 요청 예시

```text
실제 Supabase User CRUD 통합 테스트를 수행해 주세요.

조건:
- UUID 기반 고유 테스트 이메일 사용
- 회원 1명만 생성
- POST, GET ALL, GET ONE, PUT, DELETE 순서
- 모든 상태 코드 출력
- password와 키 출력 금지
- finally에서 생성한 user_id만 삭제
- 삭제 후 404 확인
- 임시 스크립트는 테스트 후 제거
```

### 14.3 예상 결과

```text
POST 201
GET_ALL 200
GET_ONE 200
PUT 200
DELETE 200
REMAINING 0
```

### 14.4 오류 진단 프롬프트

```text
Swagger에서 POST /users가 500을 반환합니다.
입력값은 검증을 통과했습니다.

키를 출력하지 말고 다음을 확인하세요.
- Supabase 연결
- 테이블과 컬럼 타입
- user_id Python 타입과 DB 반환 타입
- unique violation
- Pydantic 응답 변환
- 실제 insert 성공 후 응답 단계 실패 가능성

진단 데이터가 생성되면 반드시 삭제하세요.
```

### 14.5 완료 조건

- 실제 CRUD 전 과정 성공
- 임시 데이터 0건
- Python Schema와 DB 타입 일치

## 15. 단계 9 — 기능별 코드 리뷰

AI에게 구현이 끝난 코드를 바로 고치게 하지 말고 먼저 리뷰만 요청한다.

```text
현재 User CRUD 코드를 수정하지 말고 리뷰해 주세요.

평가 기준:
1. 코드 일관성
2. Argument와 Return 타입
3. 예외 처리
4. 공통 모듈 사용
5. 명명 규칙
6. 주석과 docstring
7. 보안
8. 테스트 누락

문제는 P0, P1, P2, P3 우선순위로 분류하고 파일과 라인을 표시하세요.
```

리뷰 결과는 다음처럼 처리한다.

- P0: PR 전에 반드시 수정
- P1: 병합 전에 수정 권장
- P2: 일정이 허용하면 수정
- P3: 향후 개선 문서에 기록

## 16. 단계 10 — 개인 브랜치 정리와 PR

### 16.1 변경 확인

```powershell
git status --short
git diff --stat
git diff --check
```

### 16.2 AI 요청 예시

```text
현재 Git 변경 상태를 읽기 전용으로 검토해 주세요.
담당 기능 PR에 포함할 파일과 제외할 파일을 구분하세요.
git add, commit, push는 아직 실행하지 마세요.
```

### 16.3 Stage 원칙

`Stage All Changes`보다 파일별 Stage를 권장한다.

포함 예시:

```text
app/routers/user_router.py
app/services/user_service.py
app/schemas/user_schema.py
sql/user.sql
```

제외 예시:

```text
.env
개인 실행 파일
팀 규칙상 제외 테스트
담당 범위 밖 계획 문서
다른 팀원의 미완성 파일
```

### 16.4 PR 방향

통합 브랜치가 `ykw`이고 개인 브랜치가 `jso`라면 다음 방향이다.

```text
base: ykw ← compare: jso
```

### 16.5 PR 본문 예시

```markdown
## 변경 사항

- User CRUD API 구현
- Supabase users 테이블 연동
- 이메일과 비밀번호 검증
- PBKDF2 비밀번호 해시
- 공개 응답에서 비밀번호 제외
- User SQL 및 테스트 추가

## 테스트

- pytest 통과
- 실제 Supabase CRUD 통과
- 테스트 데이터 정리 완료

## 확인 필요

- 공용 app/main.py에 user_router 등록
- Service Role Key 사용 정책 확인
```

## 17. 단계 11 — 5명 기능 통합

### 17.1 병합 순서

```text
공통 모듈 → User → Post → Comment → Support → Chat → Main/Deploy
```

User, Post, Comment는 외래키 관계가 있으므로 순서를 지킨다.

### 17.2 통합 담당 AI 요청

```text
현재 통합 브랜치의 전체 구조를 분석해 주세요.
아직 수정하지 마세요.

확인 항목:
- 5개 Router import 가능 여부
- Router 변수명
- 경로 충돌
- Schema 폴더명
- 공통 ApiResponse 사용
- Supabase Client 중복
- ID와 외래키 타입
- 테스트 import
- Render 실행 진입점
```

분석 후 `app/main.py` 수정만 별도 요청한다.

```text
app/main.py에 5개 Router와 /health를 등록해 주세요.
각 Router 파일은 수정하지 마세요.
Render에서 uvicorn app.main:app으로 실행 가능해야 합니다.
```

### 17.3 통합 검증

```powershell
python -m pytest -q
python -c "from app.main import app; print([route.path for route in app.routes])"
uvicorn app.main:app --reload
```

Swagger에서 다음을 확인한다.

- User
- Post
- Comment
- Support
- Chat
- Health

### 17.4 완료 조건

- 모든 import 성공
- 모든 Router 등록
- 전체 pytest 통과
- 공통 응답 일치
- API 경로 충돌 없음

## 18. 단계 12 — 통합 데이터 흐름 테스트

### 18.1 테스트 순서

```text
User 생성
→ Post 생성
→ Comment 생성
→ Support 생성
→ 각 데이터 조회 및 수정
→ Comment 삭제
→ Post 삭제
→ Support 삭제
→ User 삭제
```

### 18.2 AI 요청 예시

```text
실제 Supabase 통합 데이터 흐름을 테스트하는 임시 스크립트를 작성하고 실행해 주세요.

조건:
- 고유 prefix 사용
- 기존 데이터 수정 금지
- 생성한 모든 ID 기록
- 외래키 삭제 순서 준수
- finally에서 역순 삭제
- 키와 password 출력 금지
- 테스트 후 임시 스크립트 삭제
- 잔여 테스트 데이터 건수 보고
```

### 18.3 사람이 확인할 항목

- 없는 User로 Post를 만들 수 없는가?
- 없는 Post로 Comment를 만들 수 없는가?
- Post 삭제 시 Comment 정책이 SQL과 같은가?
- User 삭제 정책이 RESTRICT와 API 요구사항에 맞는가?

## 19. 단계 13 — Render 배포 준비

### 19.1 필요한 항목

- `app/main.py`
- `requirements.txt`
- Python 3.12.7 설정
- `/health`
- Build Command
- Start Command
- Render Environment Variables
- GitHub 통합 브랜치 또는 main

### 19.2 AI 배포 검토 요청

```text
현재 프로젝트가 Render에 배포 가능한지 읽기 전용으로 점검해 주세요.

확인 항목:
- app.main:app import
- requirements.txt 필수 패키지
- Python 3.12.7 설정
- /health
- $PORT 사용
- .env 의존 여부
- Render 환경변수 목록
- Root Directory
- 비밀값 포함 여부
- render.yaml 문법
```

### 19.3 Render 설정

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Health Check Path:

```text
/health
```

Root Directory:

```text
04_mini_project
```

저장소 루트가 이미 프로젝트 루트라면 Root Directory는 비워 둔다.

### 19.4 Render 환경변수

```text
PYTHON_VERSION=3.12.7
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
GEMINI_API_KEY
GEMINI_MODEL
```

실제 값은 Render Dashboard에서 직접 입력한다.

## 20. 단계 14 — Render 배포

### 20.1 사람의 작업

1. Render에 로그인한다.
2. New Web Service를 선택한다.
3. GitHub 저장소를 연결한다.
4. 배포 브랜치를 선택한다.
5. Root Directory를 설정한다.
6. Build Command를 입력한다.
7. Start Command를 입력한다.
8. Environment Variables를 등록한다.
9. `/health`를 Health Check Path로 설정한다.
10. Deploy를 실행한다.

AI가 로그인 정보와 실제 키를 대신 입력하게 하지 않는다.

### 20.2 배포 실패 로그 분석 요청

```text
Render 배포가 실패했습니다.
아래 로그를 분석해 주세요.

먼저 실패 원인을 한 문장으로 요약하고 다음을 구분하세요.
- 코드 오류
- import 오류
- 패키지 오류
- Python 버전 오류
- 환경변수 오류
- Root Directory 오류
- Start Command 오류

비밀값이 로그에 있으면 답변에 복사하지 마세요.
최소 수정안만 제안하세요.

[Render 로그]
```

### 20.3 자주 발생하는 오류

| 오류 | 원인 | 확인 |
|---|---|---|
| `ModuleNotFoundError: app` | Root Directory 오류 | Render Root Directory |
| `Could not import app.main` | main.py 또는 import 오류 | 로컬 import 검사 |
| `$PORT` 관련 시작 실패 | 고정 포트 사용 | Start Command |
| 환경변수 누락 | Render 변수 미등록 | Environment 메뉴 |
| Supabase 연결 실패 | URL 또는 Key 오류 | 값 재입력, 로그 비노출 |
| Gemini import 실패 | SDK 버전 불일치 | requirements 확인 |
| Python 문법 오류 | 버전 불일치 | Python 3.12.7 설정 |

## 21. 단계 15 — 배포 후 검증

### 21.1 기본 URL

```text
GET https://배포주소/health
GET https://배포주소/docs
GET https://배포주소/openapi.json
```

### 21.2 AI 테스트 요청 예시

```text
Render 배포 URL을 대상으로 읽기 및 임시 CRUD 검증 계획을 작성해 주세요.
실제 요청 전 어떤 데이터가 생성되고 삭제되는지 먼저 설명하세요.
기존 운영 데이터는 수정하지 마세요.
```

### 21.3 운영 확인 항목

- `/health` 200
- `/docs` 접근 가능
- 5개 기능 API 표시
- User 생성 201
- 전체 및 단일 조회 200
- 수정과 삭제 200
- 잘못된 입력 422
- 없는 ID 404
- 중복 이메일 409
- 응답에 password 없음
- Gemini 응답 성공
- Render 로그에 키 없음

### 21.4 완료 조건

- 배포 URL에서 핵심 기능 정상
- 임시 테스트 데이터 정리
- 로그와 응답에 비밀정보 없음

## 22. 3일 바이브 코딩 일정

## Day 1 — 분석, DB, Schema, 기본 CRUD

### 오전

1. AI에게 프로젝트 읽기 전용 분석 요청
2. 사람 검토 후 담당 범위 확정
3. 팀 공통 타입과 경로 합의
4. SQL 초안 생성 요청
5. AI SQL 리뷰 요청
6. 사람이 Supabase SQL Editor에서 실행
7. 테이블과 샘플 데이터 확인

### 오후

1. 담당별 Schema 생성 요청
2. Schema 검증 실행
3. Service 생성과 조회 구현 요청
4. Router 생성과 조회 구현 요청
5. 기본 pytest 작성 요청
6. 개인 Swagger 확인

Day 1 게이트:

- DB 생성 완료
- Schema 검증 완료
- 생성 및 조회 API 동작
- 최소 기본 테스트 통과

## Day 2 — CRUD 완성, 테스트, PR, 통합

### 오전

1. 수정과 삭제 구현 요청
2. 예외 처리 보완 요청
3. 전체 Router 테스트 작성 요청
4. pytest 실패 원인별 수정
5. 실제 Supabase 임시 CRUD
6. AI 코드 리뷰
7. P0 및 P1 수정

### 오후

1. Git 변경 범위 AI 검토
2. 담당 파일만 Stage
3. 개인 커밋과 push
4. 통합 브랜치 대상 PR 생성
5. 의존성 순서대로 병합
6. 공용 main 작성
7. 전체 pytest
8. 통합 데이터 흐름 테스트

Day 2 게이트:

- 5개 기능 통합
- 전체 Router 등록
- 전체 테스트 통과
- 실제 DB 관계 검증

## Day 3 — 배포, 운영 검증, 문서화

### 오전

1. 전체 회귀 테스트
2. 보안 검색
3. Render 배포 가능성 AI 점검
4. 사람이 Render 서비스 생성
5. 환경변수 등록
6. 1차 배포

### 오후

1. Render 로그 AI 분석
2. 최소 수정 후 재배포
3. 운영 URL 기능 검증
4. 테스트 데이터 정리
5. README와 최종 문서 작성
6. 최종 PR과 main 병합
7. 팀 데모

Day 3 게이트:

- Render 배포 성공
- `/health`와 `/docs` 정상
- 핵심 API 운영 검증
- 키와 테스트 데이터 잔여 없음

## 23. 팀원별 바이브 코딩 프롬프트 템플릿

### 23.1 User 담당

```text
담당자는 장상옥이며 범위는 User CRUD입니다.
pre_plan.md와 dev_plan.md를 먼저 읽으세요.
User Router, Service, Schema, SQL, Test만 작업하세요.
이메일 중복, 비밀번호 해시, password 응답 제외, 17자리 ID를 반드시 검증하세요.
다른 기능과 공용 main은 수정하지 마세요.
```

### 23.2 Post 담당

```text
담당 범위는 Post CRUD입니다.
User 테이블과 user_id 타입을 먼저 확인하세요.
Post 파일만 작업하고 User 코드를 수정하지 마세요.
없는 작성자와 없는 게시글의 처리를 테스트하세요.
```

### 23.3 Comment 담당

```text
담당 범위는 Comment CRUD입니다.
User와 Post의 실제 테이블명, ID 타입, 삭제 정책을 먼저 확인하세요.
없는 게시글에 댓글을 생성하지 못하도록 하고 404를 테스트하세요.
```

### 23.4 Support 담당

```text
담당 범위는 Support CRUD입니다.
상태값을 pending, answered, closed로 제한하세요.
잘못된 상태 422와 미존재 문의 404를 테스트하세요.
```

### 23.5 Chat 담당

```text
담당 범위는 Gemini Chat API입니다.
설치된 google-genai 버전을 먼저 확인하세요.
GEMINI_API_KEY와 GEMINI_MODEL을 환경변수에서 읽으세요.
테스트에서는 실제 Gemini API를 호출하지 말고 mock을 사용하세요.
```

### 23.6 통합 담당

```text
담당 범위는 공용 app/main.py, 전체 import, 전체 pytest, Render 설정입니다.
기능별 Router와 Service 로직은 임의로 수정하지 마세요.
충돌은 담당자에게 먼저 알리고 최소 범위로 해결하세요.
```

## 24. AI 변경 검토 체크리스트

AI가 파일을 수정할 때마다 다음을 확인한다.

### 파일 범위

- [ ] 요청한 파일만 변경됐는가?
- [ ] 다른 팀원의 파일이 변경되지 않았는가?
- [ ] 공용 파일 변경이 사전에 합의됐는가?
- [ ] 새 구조를 임의로 만들지 않았는가?

### 코드

- [ ] Python 3.12.7 호환인가?
- [ ] 타입 힌트가 있는가?
- [ ] Router와 Service가 분리됐는가?
- [ ] 요청과 응답 Schema가 분리됐는가?
- [ ] 함수 이름이 팀 규칙과 같은가?
- [ ] 사용하지 않는 import가 없는가?

### 예외

- [ ] 404가 필요한 곳에 있는가?
- [ ] 중복은 409인가?
- [ ] 검증 오류는 422인가?
- [ ] DB와 외부 API 오류가 노출되지 않는가?
- [ ] 오류를 무조건 성공으로 바꾸지 않았는가?

### 보안

- [ ] 실제 키가 없는가?
- [ ] password가 응답에 없는가?
- [ ] password 평문 저장이 없는가?
- [ ] 로그에 키와 password가 없는가?
- [ ] `.env`를 수정하지 않았는가?

### 테스트

- [ ] 정상 CRUD를 모두 테스트하는가?
- [ ] 404, 409, 422를 테스트하는가?
- [ ] 실제 외부 호출을 mock하는가?
- [ ] 테스트 간 상태가 독립적인가?
- [ ] 실패 테스트를 삭제하지 않았는가?

## 25. 바이브 코딩 실패 방지 규칙

### 25.1 한 번에 너무 많이 요청하지 않기

최대 한 단계 또는 한 계층씩 요청한다.

권장:

```text
User Schema만 작성
User Service만 작성
User Router만 작성
User Test만 작성
```

비권장:

```text
5개 기능과 배포까지 전부 완성
```

### 25.2 AI 완료 보고를 그대로 믿지 않기

반드시 실제 명령 결과를 확인한다.

```powershell
python -m pytest -q
python -c "from app.main import app"
git diff --check
git status --short
```

### 25.3 오류 메시지를 숨기지 않기

사용자 응답에서는 DB 오류를 숨기되 개발 중 서버 로그에서는 원인을 확인한다. AI에게 실제 키나 개인정보가 없는 오류 부분만 전달한다.

### 25.4 테스트를 약화하지 않기

테스트 실패 시 다음 행동을 금지한다.

- assert 삭제
- 예상 상태 코드를 실제 잘못된 코드로 변경
- 검증 validator 제거
- 모든 예외를 무조건 200으로 반환
- 실패 테스트 전체 skip

### 25.5 작업트리 보호

- `git reset --hard` 금지
- `git checkout --` 금지
- `git add .` 신중히 사용
- Stage All 전에 변경 파일 확인
- 사용자 파일 삭제 전 명시적 확인

## 26. 단계별 완료 보고 템플릿

AI에게 매 단계 후 다음 형식으로 보고하도록 요청한다.

```markdown
## 작업 단계

- 단계:
- 담당 기능:

## 분석한 내용

- 기존 구조:
- 적용한 규칙:

## 생성한 파일

- 경로:
- 역할:

## 수정한 파일

- 경로:
- 변경 내용:

## 실행한 검증

- 명령:
- 결과:

## 보안 확인

- 키 포함 여부:
- password 노출 여부:

## 다음 단계

- 진행할 작업:
- 팀 확인 필요 사항:
```

## 27. 최종 바이브 코딩 완료 조건

다음 조건을 모두 만족해야 작업을 완료한다.

### 기능

- [ ] User CRUD 완성
- [ ] Post CRUD 완성
- [ ] Comment CRUD 완성
- [ ] Support CRUD 완성
- [ ] Gemini Chat API 완성

### 구조

- [ ] Router, Service, Schema 분리
- [ ] 공통 Supabase Client 사용
- [ ] 공통 ApiResponse 사용
- [ ] 공용 app/main.py 존재
- [ ] 모든 Router 등록

### DB

- [ ] Supabase 테이블 생성
- [ ] PK, FK, UNIQUE, CHECK 적용
- [ ] updated_at trigger 적용
- [ ] index 적용
- [ ] 샘플 데이터 확인
- [ ] 운영 샘플 데이터 정리

### 테스트

- [ ] 기능별 pytest 통과
- [ ] 전체 pytest 통과
- [ ] 실제 Supabase 통합 테스트 통과
- [ ] Gemini mock 테스트 통과
- [ ] 운영 URL 테스트 통과
- [ ] 임시 데이터 잔여 0건

### 보안

- [ ] `.env` Git 제외
- [ ] `.env.example` placeholder
- [ ] 실제 키 검색 결과 0건
- [ ] password 응답 없음
- [ ] DB 오류 비노출
- [ ] Render Secret 등록

### 협업

- [ ] 5명 개인 브랜치 사용
- [ ] PR로 통합
- [ ] 담당 범위 밖 변경 없음
- [ ] 리뷰 완료
- [ ] 통합 브랜치 테스트 완료
- [ ] main 최종 병합 완료

### 배포

- [ ] Python 3.12.7 설정
- [ ] Render Build 성공
- [ ] `$PORT` 사용
- [ ] `/health` 200
- [ ] `/docs` 접근 가능
- [ ] 주요 API 정상
- [ ] 배포 로그 비밀값 없음

## 28. 권장 실행 요약

```text
계획 문서 읽기
→ 프로젝트 읽기 전용 분석
→ 팀 공통 규칙 확정
→ SQL 작성 및 사람 검토
→ Supabase SQL 수동 실행
→ Schema 작성 및 검증
→ Service 작성 및 테스트
→ Router 작성 및 테스트
→ 실제 Supabase 임시 CRUD
→ AI 코드 리뷰
→ 담당 파일만 Stage
→ 개인 브랜치 PR
→ 통합 브랜치 순차 병합
→ 공용 main 등록
→ 전체 pytest
→ Render 배포 점검
→ 사람이 환경변수 입력 및 배포
→ 운영 URL 테스트
→ 문서화 및 최종 병합
```

바이브 코딩의 목표는 AI가 모든 결정을 대신하는 것이 아니라, 사람이 계획과 검증을 통제하면서 반복 작업을 빠르고 안전하게 구현하는 것이다.

