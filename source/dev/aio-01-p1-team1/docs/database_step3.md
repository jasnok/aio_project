# 3단계: 데이터베이스와 시연 자료

클라우드와 로컬 Supabase에서 **가상 공고 15개를 이용한 시연 준비와 검증을 마쳤습니다.** 로컬에서는 PostgreSQL·Auth·Storage·REST API를 Docker로 실행합니다. 최초 설치에 인터넷 연결이 필요하지만, 준비된 뒤 공고 검색·이미지 조회는 로컬 주소를 사용합니다.

## 준비한 시연 자료

기준일은 **2026-09-28**입니다. 강남구·마포구·노원구·송파구·은평구에 각각 3개씩, 총 15개의 가상 공고가 있습니다.

| 구분 | 구성 |
|---|---|
| 신청 기간 | 신청 예정 5개 / 모집 중 5개 / 마감 5개 |
| 이미지 | 이미지 없음 5개 / 한 장 5개 / 세 장 5개 |
| 이미지 저장 | 코드로 만든 가상 평면도 PNG 3개를 공고에서 함께 사용, 연결 기록 20개 |
| 금액·면적 | 서로 다른 값으로 검색과 정렬을 확인 |
| 개인정보 | 실제 이름·연락처·상세 주소 없음 |

제목·설명에 `포트폴리오 시연용 가상 공고`라고 표시했습니다. 실제 모집 정보가 아닙니다. 도면도 실제 주택 도면이 아닙니다.
원문 주소 칸은 샘플 식별에 사용하는 `example.invalid` 주소이며, 두 목록 화면에서는 원문 이동 버튼 대신 시연 자료라는 안내를 표시합니다.

## 실행 명령

저장소 최상위 폴더에서 실행합니다. 연결 대상은 기존 `BE/.env`와 환경변수 설정입니다.

```powershell
# 저장하지 않고 준비될 내용을 먼저 확인
.\BE\.venv\Scripts\python.exe -X utf8 BE/scripts/seed_demo.py --date 2026-09-28

# 실제 등록 — 현재 프로젝트에는 이미 실행했습니다
.\BE\.venv\Scripts\python.exe -X utf8 BE/scripts/seed_demo.py --date 2026-09-28 --apply

# DB 필수 항목과 시연 공고·이미지 관계를 읽기 전용 확인
.\BE\.venv\Scripts\python.exe -X utf8 BE/scripts/check_database.py
```

등록 명령은 처음에 `created: 15`, 두 번째에는 `created: 0, reused: 15`를 반환했습니다. 공고 ID와 이미지 파일 이름을 재사용합니다. 기본 재실행은 날짜나 공고 본문을 바꾸지 않습니다.

시간이 지나 모집 상태를 다시 준비하고 싶다면 기준일을 지정해 **시연 공고의 날짜와 설명**을 갱신할 수 있습니다.

```powershell
# 예: 이 날짜를 중심으로 예정·모집 중·마감 상태를 다시 구성
.\BE\.venv\Scripts\python.exe -X utf8 BE/scripts/seed_demo.py --date 2026-10-15 --refresh-dates --apply
```

실제 공고의 모집 날짜를 바꾸는 명령이 아닙니다. 시연 식별 주소와 제목·설명 표식이 모두 맞는 자료만 대상으로 합니다. 해당 주소가 기존 일반 공고와 충돌하거나 중복되어 있으면 쓰기 전에 중단합니다. 이미지 업로드 도중 실패해도 같은 명령을 재실행하면 이미 만든 공고를 재사용합니다.

한 PC에서 같은 프로젝트로 동시에 실행하는 것은 잠금으로 막습니다. **여러 PC에서 동시에 샘플 등록을 실행하는 것은 지원하지 않습니다.** 관리자가 등록 작업을 한 번씩 실행하는 도구입니다. DB 전체 초기화나 기존 공고 삭제 기능은 없습니다. 샘플 이미지 3개는 여러 공고가 함께 참조하므로 Storage에서 임의로 삭제하지 마세요.

## 데이터베이스 설치 순서

[SQL 적용 안내](../BE/sql/README.md)에 최초 설치 파일과 과거 변경 파일의 차이를 정리했습니다.

1. 새 프로젝트에는 `BE/sql/bootstrap_portfolio.sql`로 테이블을 준비합니다.
2. `supabase/migrations/20260928000100_image_bucket.sql`로 이미지 저장소를 준비합니다.
3. 설정 점검 후 샘플 등록 도구를 실행합니다.

현재 클라우드에는 이미 테이블과 저장소가 있으므로 1·2를 다시 실행할 필요가 없습니다. 이번 3단계에서는 클라우드 테이블을 삭제·재생성하거나 권한을 변경하지 않았습니다.

로컬 CLI에서는 `supabase/migrations`에 있는 두 파일을 이름 순서로 적용합니다. 첫 파일은 초기 스키마의 동일 사본입니다. 테스트로 두 파일의 일치를 확인합니다. 앞으로 변경할 때는 새 마이그레이션 파일을 추가합니다. 과거 SQL들을 전부 실행하는 방식은 사용하지 않습니다.

## 로컬 DB: 2026-09-28 실행 검증 완료

2026-09-24에는 CLI 다운로드·실행 명령이 차단됐습니다. 이번에는 [Supabase 공식 GitHub 릴리스](https://github.com/supabase/cli/releases/tag/v2.118.0)의 Windows 2.118.0 ZIP을 고정해 다운로드했고, GitHub 릴리스가 제공한 SHA-256 해시와 일치함을 확인한 뒤 실행했습니다. CLI와 검증 기록은 Git에서 제외되는 `.runtime/tools/`에만 있습니다. 다른 컴퓨터에서 이 저장소를 받아 실행하려면 [공식 설치 안내](https://supabase.com/docs/guides/local-development/cli/getting-started)에 따라 CLI를 준비해야 합니다.

준비한 파일은 다음과 같습니다.

- `supabase/config.toml`: 이 저장소만 사용하는 로컬 프로젝트 설정. 기본 포트는 API 54321, DB 54322입니다.
- `supabase/migrations/`: 초기 테이블과 이미지 저장소 준비 SQL.
- `scripts/local_db.ps1`: 로컬 DB 시작·상태 확인·종료. 클라우드 연결이나 초기화 명령은 포함하지 않습니다.
- `scripts/start_local_demo.ps1`: 해당 터미널에서만 로컬 URL과 로컬 키를 사용해 세 앱 중 하나를 시작합니다. 기존 클라우드 `.env`를 고치지 않습니다.

저장소 최상위 폴더에서 로컬 DB를 시작합니다. 최초 시작 시 Docker 이미지 다운로드에 인터넷과 디스크 여유가 필요합니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local_db.ps1 -Action Start
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local_db.ps1 -Action Status
```

`Status`에는 로컬 키가 표시될 수 있으므로 화면을 공개하지 마세요. DB에 가상 공고를 넣고 확인합니다. 아래 두 명령은 로컬 URL·키를 해당 PowerShell 창에만 넣고 실행한 예입니다. 키 값은 출력하거나 파일에 저장할 필요가 없습니다.

```powershell
$localStatus = .\.runtime\tools\supabase.exe status -o json | ConvertFrom-Json
$env:SUPABASE_URL = $localStatus.API_URL
$env:SUPABASE_SERVICE_ROLE_KEY = $localStatus.SERVICE_ROLE_KEY
.\BE\.venv\Scripts\python.exe -X utf8 BE/scripts/seed_demo.py --date 2026-09-28 --apply
.\BE\.venv\Scripts\python.exe -X utf8 BE/scripts/check_database.py
```

앱은 터미널 세 개에서 하나씩 시작합니다. 현재 PC에서 8000 포트가 이미 사용 중이어서 아래는 비어 있는 대체 포트를 사용합니다. 각 터미널의 시작 폴더는 저장소 최상위입니다. AI 상담의 임시 대화 기록을 확인하려면 백엔드를 시작하기 전에 이 프로젝트 전용 로컬 Redis도 시작합니다. 다른 프로젝트가 쓰는 6379 포트는 건드리지 않고 16379 포트만 사용합니다. 로컬 실행 스크립트는 AI를 `mock` 모드로 고정하므로 유료 Gemini 요청을 보내지 않습니다.

관리자 API는 이제 로그인 후 받은 1시간짜리 토큰을 요구합니다. 로컬 실행 스크립트가 `.runtime/admin-token-secret`을 안전하게 생성·재사용합니다. 이전에 로그인해 둔 브라우저 탭은 로그아웃하고 다시 로그인하세요. 일반 실행에서는 [설정 안내](configuration.md)의 `ADMIN_TOKEN_SECRET`이 필요합니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local_redis.ps1 -Action Start
```

```powershell
# 터미널 1: API 서버
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_local_demo.ps1 -App BE -Port 18000
```

```powershell
# 터미널 2: 사용자 화면 http://127.0.0.1:18501
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_local_demo.ps1 -App FE_User -Port 18501 -BackendPort 18000
```

```powershell
# 터미널 3: 관리자 화면 http://127.0.0.1:18502
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_local_demo.ps1 -App FE_Admin -Port 18502 -BackendPort 18000
```

각 앱은 터미널에서 `Ctrl+C`로 종료합니다. 모든 작업을 마치고 Redis와 로컬 DB를 정상 종료하려면 다음을 실행합니다. 일반 `Stop`은 데이터를 유지합니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local_redis.ps1 -Action Stop
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local_db.ps1 -Action Stop
```

로컬 검증에서는 같은 가상 공고 15개를 두 번 등록해 첫 실행 `created=15`, 두 번째 `created=0`을 확인했습니다. 회원가입 시 프로필 자동 생성, 일반 공개키의 관리자 테이블 접근 거부, 이미지 3개의 HTTP 200, 로컬 API의 목록·검색, 두 화면 코드의 조회·등록을 확인했습니다. 검사 중 만든 임시 계정과 임시 공고는 각각 확인한 ID로 정리했습니다. 로컬 DB를 **Stop → Start**한 후에도 공고 15개와 이미지 연결 20개, 공개 이미지 3개가 유지됐습니다. 세 앱 모두 `start_local_demo.ps1`로 기동 확인했습니다.

현재 로컬 구성에서는 메모리를 아끼기 위해 Studio·실시간 서비스·메일 미리보기 등을 실행하지 않습니다. 주소가 없는 가상 공고의 지도 위치는 표시하지 않습니다. 사용자 화면의 AI 안내원과 AI 상담은 로컬 `mock` 모드에서 검증할 수 있으며, AI 상담에는 위 Redis 컨테이너가 필요합니다. 관리자 화면의 PDF/HWPX 자동 추출은 별도 기능으로 Gemini API 키가 필요합니다. 무료 사용 한도와 계정의 과금 설정은 본인 Google AI Studio에서 확인해야 합니다. 키가 없으면 수동 등록이나 자동 등록 화면의 가상 샘플 재생을 사용할 수 있습니다. [후속 로컬 시연 검증](local_demo_validation.md)에 월세 보정·등록 시연과 새 저장 함수 적용 방법을 정리했습니다.

## 이번에 확인한 결과

| 검사 | 결과 |
|---|---|
| 테이블 7개에서 앱이 사용하는 칼럼 조회 | 통과 |
| 공고↔이미지, 즐겨찾기↔공고 관계 조회 | 통과 |
| 샘플 등록 후 재실행 | 15개 유지, ID 동일, 이미지 파일 3개 유지 |
| 샘플의 이미지 수 분포 | 0장·1장·3장 각각 5개 |
| 사용자 화면 | 실제 API와 연결한 AppTest로 목록·상세 요소·마포구 검색 3건·보증금 정렬 선택 확인 |
| 관리자 화면 | 실제 API와 연결한 AppTest로 목록 표시·입력 폼 제출·DB 등록 확인 |
| 등록 확인용 임시 공고 | 검증용 고유 주소와 ID로 확인 후 해당 1건만 정리 |
| API 서버 재시작 | 공고 ID·이미지 연결 동일, 목록 API 정상 응답 |
| 공개 이미지 주소 | 3개 모두 HTTP 200 |
| `.env` 3개 | 작업 전후 파일 해시 동일 |
| 자동 테스트 | BE 184 + 관리자 333 + 사용자 158 + 공통 설정 13 = **688개 통과** |

AppTest는 실제 Streamlit 페이지 코드를 실행하는 테스트 도구입니다. 브라우저 화면의 시각적 배치나 로그인 세션 복원 전체를 검사한 것은 아닙니다. 관리자 테스트에서는 테스트 세션에 로그인 상태를 지정했으므로 실제 계정 로그인 검증은 포함하지 않습니다. 또한 현재 DB 칼럼과 API 응답의 호환성을 확인했지만 모든 SQL 자료형·인덱스·권한 정책을 재감사한 것은 아닙니다.

테스트는 기존 실행 안내의 `scripts/run_tests_offline.py`로 다시 실행할 수 있습니다. 새 테스트는 중복 방지·중간 실패 후 복구·기존 공고 보존·식별자 충돌·날짜 갱신·마이그레이션 사본 일치를 확인합니다.

인터넷 공개 전에는 기존 관리자·사용자 API 인증과 권한 문제를 보완해야 합니다. 지도와 AI 상담의 추가 설정은 [2단계 설정 안내](configuration.md)에 있습니다.
