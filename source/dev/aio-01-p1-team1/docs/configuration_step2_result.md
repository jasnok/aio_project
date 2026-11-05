# 2단계 완료 기록 — 2026-09-24

## 완료한 범위

세 앱의 설정 읽기를 공통 패키지로 통일했습니다. 환경변수 → 앱 `.env` → 화면 앱 Secrets → 기본값 순서입니다. 관리자 화면에서도 `.env`의 서버 주소를 읽고, 일부 항목만 들어 있는 `.env` 때문에 배포 Secrets가 무시되지 않도록 했습니다. BE의 CORS와 상담 요약 저장 방식도 같은 설정 규칙을 따릅니다.

설정 예시, 설치·실행 스크립트, 비밀값을 출력하지 않는 점검 도구, [비전공자용 설정 안내](configuration.md)를 추가했습니다. 관리자 계정 생성 시 비밀번호를 명령줄 인자로 받던 방식을 숨김 입력으로 바꾸고 저장된 암호 해시 출력도 제거했습니다.

사용자가 입력한 `.env` 3개는 작업 전후 파일 해시가 같음을 확인했습니다. 실제 키를 코드나 문서에 옮기지 않았습니다. 기존 개인 문서 3개와 1단계 보존 자료는 유지했습니다.

## 검증 결과

| 항목 | 결과 |
|---|---|
| BE 테스트 | 175개 통과 |
| 관리자 화면 로직 테스트 | 333개 통과 |
| 사용자 화면 로직 테스트 | 158개 통과 |
| 공통 설정 테스트 | 13개 통과 |
| 합계 | **679개 통과** — 기존 659개 + 신규 20개 |
| 세 가상환경의 패키지 의존성 검사 | 모두 `pip check` 통과 |
| 실행 스크립트 실제 기동 | BE·두 Streamlit 서버 모두 정상 응답 |
| 실제 서버의 공고 페이지 조회 | HTTP 200, 성공 응답 |
| Supabase 테이블 7개 / 이미지 저장소 / Auth | 읽기 연결 모두 HTTP 200 |
| 공고·이미지 관계 조회 / 공개키의 관리자 테이블 접근 | 관계 조회 성공 / 공개키 접근 거부 확인 |
| 관리자 Gemini 모델 접근 | HTTP 200 — 실제 답변 생성은 미검증 |
| 카카오 Local API | HTTP 403 — 앱의 카카오맵 사용 설정 확인 필요 |
| BE Gemini 키 / Redis 주소 | 미설정 — 사용자 AI 상담의 남은 준비 항목 |

테스트에서는 외부 TCP 연결을 차단했습니다. BE 오류 처리 테스트의 외부 로그 연결 시도 19번은 차단됐고 테스트는 통과했습니다. 기존 Starlette 테스트 클라이언트의 사용 중단 예고 경고는 남아 있습니다. 설치 과정에서는 누락된 BE의 Gemini·Redis 패키지를 설치하고, 어떤 설치 패키지도 의존하지 않는 구형 `supafunc` 잔여 패키지를 제거해 버전 충돌을 해소했습니다.

실행 확인에는 다른 앱의 포트와 겹치지 않게 임시 포트 18000/18501/18502를 사용했습니다. 점검용 프로세스는 종료했습니다. Streamlit 서버의 정상 응답을 확인한 것이며, 브라우저의 회원가입·로그인·등록·삭제 전체 흐름까지 확인한 것은 아닙니다.

## Supabase 준비

2026-09-23에 사용자 요청으로 `profiles`, `admins`, `listings`, `favorites`, `listing_images`, `logs`, `chat_summaries` 테이블과 프로필 자동 생성 트리거를 생성했습니다. 테이블 7개에 RLS를 적용하고, 테이블 데이터 API 권한을 서버용 역할에 부여했습니다. `listing-images` 저장소는 공개 공고 이미지, 5MB, JPEG/PNG/WebP로 준비했습니다.

회원 생성 시 프로필 생성과 관련 테이블 삽입을 트랜잭션 안에서 확인한 뒤 롤백했습니다. 그 검사에서 만든 임시 계정·공고·즐겨찾기 등은 남기지 않았습니다. 실제 관리자 계정과 시연용 공고는 아직 생성하지 않았습니다. 재현용 SQL은 [bootstrap_portfolio.sql](../BE/sql/bootstrap_portfolio.sql)에 있습니다.

## 다시 확인하는 방법

저장소 최상위 폴더에서 설정 점검을 실행합니다.

```powershell
.\BE\.venv\Scripts\python.exe -X utf8 scripts/check_settings.py --online
.\BE\.venv\Scripts\python.exe -m unittest discover -s packages/housing-config/tests -q
```

앱 테스트는 각 폴더에서 전용 도구로 실행합니다. 다음은 저장소 최상위 폴더에서 시작하는 명령입니다.

```powershell
Push-Location BE
.\.venv\Scripts\python.exe ../scripts/run_tests_offline.py
Pop-Location
Push-Location FE_Admin
.\.venv\Scripts\python.exe ../scripts/run_tests_offline.py
Pop-Location
Push-Location FE_User
.\.venv\Scripts\python.exe ../scripts/run_tests_offline.py
Pop-Location
```

외부 연결 차단은 이 테스트 프로세스 안에서만 적용됩니다. 결과는 Git에서 제외되는 `.runtime/tests-앱이름.json`에 저장됩니다. 설정 점검 결과도 필요하면 `--json .runtime/settings-check.json`으로 저장할 수 있습니다.

## 완료와 남은 설정의 구분

**2단계인 실행 설정 통일은 완료했습니다.** 카카오 권한 활성화, BE의 AI 키·Redis 준비, 본인이 정할 관리자 계정 생성은 [설정 안내](configuration.md)의 절차를 따르면 됩니다. 이 항목들이 준비되기 전에는 모든 선택 기능이 동작한다고 볼 수 없습니다.

권한 검사 보완, 로컬 DB 전체 재현, 시연 데이터, Redis 없는 상담과 인터넷 공개 배포는 후속 작업입니다. 이번 테스트 통과를 공개 배포 가능 판정으로 사용하지 않습니다.
