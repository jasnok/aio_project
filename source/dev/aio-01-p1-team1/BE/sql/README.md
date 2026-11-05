# SQL 적용 순서

## 새 프로젝트

1. `bootstrap_portfolio.sql`: 현재 앱의 테이블 7개·관계·제약·RLS·프로필 트리거.
2. `../../supabase/migrations/20260928000100_image_bucket.sql`: 이미지 저장소.
3. 저장소 최상위에서 `BE/.venv/Scripts/python.exe scripts/check_settings.py --online`.
4. `BE/.venv/Scripts/python.exe BE/scripts/seed_demo.py --apply`.

현재 연결된 클라우드 프로젝트는 기존 테이블·이미지 버킷이 준비되어 있습니다.
기존 DB에서 이번 백엔드를 실행하려면
`../../supabase/migrations/20260930000100_atomic_listing_save.sql`을 먼저 적용해야 합니다.
이번 검증에서는 로컬 DB에만 적용했습니다. 원격 DB를 초기화하지 않습니다.

## 로컬 CLI

`supabase/migrations`의 타임스탬프 순서로 적용합니다.
`bootstrap_portfolio.sql`은 초기 테이블과 후속 공고 저장 함수를 함께 포함하며,
자동 테스트가 해당 마이그레이션들의 내용과 일치하는지 확인합니다.
새 변경은 다음 날짜의 별도 SQL을 추가합니다. 이미 적용한 마이그레이션을 수정하지 않습니다.

기존 로컬 DB에는 저장소 루트에서 `supabase migration up --local`을 실행합니다.
원자 저장 회귀 검증은 로컬 컨테이너에서 다음과 같이 실행합니다. 임시 자료와 제약은 모두 롤백됩니다.

```powershell
Get-Content BE/sql/tests/atomic_listing_save.sql -Raw |
    docker exec -i supabase_db_housing-portfolio-local psql -U postgres -d postgres -v ON_ERROR_STOP=1
```

## 과거 파일

성능 개선 SQL은 `supabase/migrations/20261001000100_performance_queries.sql`에 있습니다. 검색·순위 RPC는 백엔드의 `service_role`만 실행할 수 있습니다. 로컬 적용 후 `BE/sql/tests/performance_queries.sql`을 위와 같은 psql 명령으로 실행하면 임시 자료를 롤백하면서 검색·집계·권한을 검사합니다.

`schema.sql`, `alter_listings*.sql`, `profiles.sql`, `logs.sql`,
`create_listing_images.sql`은 팀 프로젝트의 변경 기록으로 보존합니다.
최신 설치 절차에서는 이들을 함께 실행하지 않습니다. 내용이 겹치며 최종 구조와도 다를 수 있습니다.

`CREATE TABLE IF NOT EXISTS`는 기존 테이블의 누락 항목을 보완하지 않습니다.
다른 DB의 구조가 다르면 데이터 보존을 고려한 별도 변경 SQL부터 작성합니다.
