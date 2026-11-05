# 2단계: 실행 설정 안내

2단계는 **주소와 열쇠를 읽는 방법을 세 프로그램에서 통일하는 작업**입니다. `.env`는 접속 주소와 비밀키를 적어 두는 개인 설정표라고 생각하면 됩니다. 이번 작업은 설정 정리이며, 인증 보완·샘플 데이터·Redis 없는 상담·전체 공개 배포는 후속 작업입니다.

## 1. 어떤 파일을 수정하나요?

| 파일 | 기본 실행에 필요한 항목 | 해당 기능을 쓸 때만 필요한 항목 |
|---|---|---|
| `BE/.env` | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `ADMIN_TOKEN_SECRET` | 지도: `KAKAO_REST_API_KEY`; 상담: `REDIS_URL`; 실제 AI: `GEMINI_API_KEY`, `CHAT_GEMINI_MODE=gemini` |
| `FE_User/.env` | `SUPABASE_URL`, `SUPABASE_ANON_KEY` | 서버 주소가 달라지면 `BACKEND_URL` |
| `FE_Admin/.env` | 로컬 기본 실행에는 없음 | 문서 AI 분석: `GEMINI_API_KEY`; 서버 주소가 달라지면 `BACKEND_URL` |

이미 입력한 `.env`는 덮어쓰지 마세요. 새로 설치하는 사람은 각 폴더의 `.env.example`을 `.env`로 복사하고 자신의 값을 입력합니다. 예시 파일에는 실제 키가 없습니다. Service Role Key는 BE에만 둡니다.

관리자 로그인이 발급하는 1시간짜리 토큰은 `ADMIN_TOKEN_SECRET`으로 서명합니다. 일반 실행에는 32바이트 이상 무작위 값을 `BE/.env`에 직접 입력하고 외부에 공개하지 마세요. 로컬 시연용 `start_local_demo.ps1`은 `.runtime/admin-token-secret`에 무작위 값을 한 번 만들어 재사용하므로 직접 입력할 필요가 없습니다. 기존 브라우저에 남은 예전 관리자 로그인 표시는 새 인증 정보가 아니므로 다시 로그인해야 합니다.

일반 실행용 값을 만들 때는 저장소 최상위에서 `BE\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"`를 실행하고, 출력된 값을 본인 PC의 `BE/.env`에만 붙여 넣으세요. 예시 파일의 `your-...` 값은 서버에서 거절합니다.

설정은 **운영체제 환경변수 → 해당 앱의 `.env` → Streamlit Secrets → 기본값** 순서로 읽습니다. 앞의 값이 비어 있으면 다음 위치를 확인합니다. BE에는 Streamlit Secrets가 없습니다. `.env` 내용은 운영체제 환경변수로 복사하지 않습니다.

값을 바꾼 뒤 해당 프로그램을 종료하고 다시 실행하세요. 일부 연결과 API 주소는 시작할 때 보관합니다. 변경이 반영되지 않으면 같은 이름의 환경변수가 있는지도 확인합니다. 비밀번호에 `$` 등이 있어도 임의로 치환하지 않습니다. `#` 등이 포함된 값은 따옴표로 감싸 주세요.

## 2. 설치와 실행

Windows PowerShell에서 **저장소 최상위 폴더**를 기준으로 실행합니다. Python 3.11 이상이 필요합니다. 공통 설정 패키지를 함께 설치하므로 이전처럼 BE 안에서 requirements만 설치하면 안 됩니다.

```powershell
cd C:\dev\aio-01-p1-team1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

설치 명령은 각 앱의 `.venv`에 필요한 패키지를 설치합니다. `.env` 생성·덮어쓰기는 하지 않습니다. `-ExecutionPolicy Bypass`는 이 명령 실행에만 적용되며 컴퓨터 전체 정책을 변경하지 않습니다.

터미널을 세 개 열어 각각 같은 최상위 폴더에서 실행합니다.

```powershell
# 터미널 1: 서버
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1 -App BE
```

```powershell
# 터미널 2: 사용자 화면
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1 -App FE_User
```

```powershell
# 터미널 3: 관리자 화면
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1 -App FE_Admin
```

| 프로그램 | 접속 주소 |
|---|---|
| API 문서 | http://127.0.0.1:8000/docs |
| 사용자 화면 | http://127.0.0.1:8501 |
| 관리자 화면 | http://127.0.0.1:8502 |

종료는 각 터미널에서 `Ctrl+C`를 누릅니다. 포트를 이미 다른 앱이 사용 중이면 해당 앱을 임의로 종료하지 말고 `-Port 8511`처럼 다른 포트를 지정하세요. BE 포트를 바꾸면 두 화면의 `BACKEND_URL`도 새 서버 주소로 맞춥니다. 실행 스크립트는 본인 컴퓨터에서만 접속하도록 설정되어 있습니다.

## 3. 설정을 직접 점검하는 방법

```powershell
# 인터넷 연결 없이 설정 누락과 주소 형식 확인
.\BE\.venv\Scripts\python.exe -X utf8 scripts/check_settings.py

# 외부 서비스의 읽기 연결까지 확인
.\BE\.venv\Scripts\python.exe -X utf8 scripts/check_settings.py --online
```

- `PASS`: 해당 검사 통과. 설정 읽기 성공과 실제 연결 성공은 서로 다른 검사입니다.
- `WARN`: 선택 기능의 설정 누락 또는 연결 문제. 공고 조회 등과 구분합니다.
- `FAIL`: 기본 실행에 필요한 설정/연결 문제. 종료 코드도 1이 됩니다.
- `INFO`: 현재 모드 설명입니다.

키나 비밀번호, 서버 응답 본문은 결과에 출력하지 않습니다. 온라인 점검은 데이터 등록·삭제나 Gemini 답변 생성을 하지 않습니다. 지도 주소 조회와 서비스 읽기 요청은 발생합니다. 이 명령은 앱의 로그인부터 등록까지 전체 사용 흐름을 검사하는 도구는 아닙니다.

## 4. 현재 직접 설정할 부분

### 카카오 지도

2026-09-24 재점검에서 카카오 Local API가 HTTP 403을 반환했습니다. 앞선 확인에서는 앱의 `OPEN_MAP_AND_LOCAL` 서비스가 꺼져 있다는 응답이었습니다.

1. [Kakao Developers](https://developers.kakao.com/)에 로그인합니다.
2. 키를 발급한 앱을 선택합니다.
3. **카카오맵 → 사용 설정**에서 사용 상태를 확인하고 활성화합니다.
4. 온라인 점검 명령을 다시 실행해 `Kakao Local: HTTP 200`인지 확인합니다.

현재 키를 새로 발급할 필요가 있다는 뜻은 아닙니다. 활성화 후에도 403이면 앱 권한을 확인합니다. 메뉴 안내는 [카카오맵 공식 문서](https://developers.kakao.com/docs/ko/kakaomap/common)를 참고하세요.

### 실제 AI 상담

관리자 화면의 Gemini 키는 읽기 연결 확인에 통과했습니다. 다만 **관리자 문서 분석**과 **사용자 AI 상담**은 서로 다른 프로그램이므로 BE에도 키가 필요합니다.

상담까지 실행하려면 `BE/.env`에 아래 항목을 직접 추가합니다. 실제 키는 채팅에 보내지 말고 파일 안에서 입력하세요.

```dotenv
CHAT_GEMINI_MODE=gemini
GEMINI_API_KEY=여기에_본인_Gemini_키
GEMINI_MODEL=여기에_사용할_모델명
REDIS_URL=redis://127.0.0.1:6379/0
```

모델명은 현재 관리자 `.env`에서 쓰는 접근 가능한 모델명을 사용할 수 있습니다. 마지막 주소는 **로컬 Redis 서버를 실제로 실행했을 때만** 유효한 예시입니다. 주소만 적는다고 서버가 설치되지는 않습니다. 이미 준비한 Redis가 있다면 그 서버의 TCP 연결 주소를 입력합니다. 현재 코드에서는 `mock` 상담도 대화 기록 때문에 Redis가 필요합니다. Redis 없이 상담하는 개선은 이번 설정 통일에 포함하지 않았습니다.

`CHAT_SUMMARY_STORAGE=preview`는 요약을 실행 중인 서버 메모리에만 저장합니다. 재시작 후에도 요약을 남기려면 `supabase`를 선택합니다. `GEMINI_API_KEY` 접근 성공은 실제 답변 생성 성공이나 무료 사용량 잔여를 보장하지 않습니다. 생성 요청은 이번 점검에서 하지 않았습니다.

### 관리자 계정

테이블만 생성했으며 관리자 아이디와 비밀번호는 임의로 만들지 않았습니다. 사용할 아이디를 정한 뒤 다음을 실행합니다.

```powershell
.\BE\.venv\Scripts\python.exe BE/scripts/create_admin.py 본인이정한아이디
```

이어지는 입력창에 비밀번호를 두 번 입력합니다. 입력 중 글자가 보이지 않는 것이 정상입니다. 비밀번호와 저장된 암호 해시는 결과에 출력하지 않습니다. 한 번 만든 아이디로 다시 만들면 중복 오류가 나므로, 최초 한 번만 실행하세요.

사용자 회원가입은 Supabase Auth를 사용합니다. 현재 프로젝트는 이메일 확인이 켜져 있으므로 가입 메일 인증 후 로그인합니다. 메일 전송 제한은 별도 서비스 설정이며 [Supabase 이메일 안내](https://supabase.com/docs/guides/auth/auth-smtp)를 확인합니다.

## 5. Supabase에 준비한 내용

`profiles`, `admins`, `listings`, `favorites`, `listing_images`, `logs`, `chat_summaries` 7개 테이블과 회원가입 시 프로필 생성 트리거를 준비했습니다. 모든 테이블은 RLS가 활성화되어 있고, 데이터 API 접근은 BE의 service_role을 사용합니다. 일반 공개키로 테이블을 직접 읽는 권한은 부여하지 않았습니다.

`listing-images` 저장소는 공고 이미지를 공개해서 표시하기 위한 저장소입니다. JPEG/PNG/WebP, 파일당 최대 5MB로 설정했습니다. 개인 문서를 올리는 용도가 아닙니다.

새 프로젝트를 준비할 때는 `BE/sql/bootstrap_portfolio.sql`을 SQL Editor에서 실행합니다. 기존 테이블 구조를 변경하는 마이그레이션 파일이 아니므로 이미 운영 중인 DB에 적용해 구조가 자동으로 맞춰질 것으로 기대하면 안 됩니다. 이미지 저장소는 Storage에서 위 설정으로 별도 생성합니다. 현재 연결된 프로젝트에는 이미 준비했으므로 다시 실행할 필요가 없습니다.

## 6. 배포할 때의 설정

화면 앱의 `.streamlit/secrets.toml.example`은 배포 Secrets에 입력할 예시입니다. 실제 `.env`와 `secrets.toml`은 Git에서 제외됩니다. 클라우드에서는 `BACKEND_URL`을 실제 BE 주소로 변경하고, 저장소 전체와 공통 패키지를 함께 설치해야 합니다.

현재 관리자·사용자 API 권한 검사는 후속 개선이 필요합니다. **이번 단계 완료는 인터넷 공개 배포 완료를 뜻하지 않습니다.** RLS와 로컬 CORS 설정만으로 서버 API 권한 문제가 해결되지는 않습니다.
