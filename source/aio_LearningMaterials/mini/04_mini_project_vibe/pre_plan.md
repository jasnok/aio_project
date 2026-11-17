# User CRUD 프로젝트 사전 개발 계획서

## 1. 문서 개요

### 1.1 목적

이 문서는 FastAPI, Pydantic, Supabase PostgreSQL을 이용하여 User CRUD API를 개발하기 위한 사전 계획서다. 개발을 시작하기 전에 기능 범위, 데이터 구조, API 계약, 예외 처리, 보안 기준, 테스트 방법과 완료 조건을 합의하는 것을 목적으로 한다.

### 1.2 담당 정보

- 담당자: 장상옥
- 담당 기능: User CRUD
- 개발 언어: Python 3.12.7
- 웹 프레임워크: FastAPI
- 데이터 검증: Pydantic v2
- 데이터베이스: Supabase PostgreSQL
- 데이터베이스 클라이언트: Supabase Python SDK
- 테스트: pytest, FastAPI TestClient
- 환경변수: python-dotenv

### 1.3 개발 범위

다음 기능을 구현한다.

1. 회원 생성
2. 회원 전체 조회
3. 회원 단일 조회
4. 회원 전체 정보 수정
5. 회원 삭제
6. 이메일 형식 검증
7. 이메일 중복 방지
8. 비밀번호 해시 저장
9. 공개 응답에서 비밀번호 제외
10. 공통 API 응답 적용
11. Supabase 연동
12. 단위 테스트와 실제 연동 테스트

다음 기능은 이번 담당 범위에서 제외한다.

- 로그인과 로그아웃
- JWT 발급 및 검증
- 이메일 인증
- 비밀번호 찾기
- 관리자 권한
- Post, Comment, Support CRUD
- Gemini Chat API

## 2. 목표 및 완료 기준

### 2.1 기능 목표

클라이언트는 `/users` API를 통해 회원을 생성, 조회, 수정, 삭제할 수 있어야 한다. 모든 입력값은 Pydantic으로 검증하고, 실제 데이터 처리는 Service 계층에서 수행한다.

### 2.2 완료 기준

- `POST /users`가 정상 입력에 대해 201을 반환한다.
- `GET /users`가 회원 목록을 반환한다.
- `GET /users/{user_id}`가 회원 한 명을 반환한다.
- `PUT /users/{user_id}`가 회원 정보를 수정한다.
- `DELETE /users/{user_id}`가 회원을 삭제한다.
- 존재하지 않는 ID는 404로 처리한다.
- 중복 이메일은 409로 처리한다.
- 잘못된 요청은 422로 처리한다.
- 내부 DB 오류는 상세 내용을 숨기고 500으로 처리한다.
- 비밀번호는 평문으로 저장하지 않는다.
- 모든 공개 응답에서 `password`를 제외한다.
- pytest가 모두 통과한다.
- 실제 Supabase CRUD 연동을 임시 데이터로 검증한 후 데이터를 정리한다.
- `.env`와 비밀키가 Git에 포함되지 않는다.

## 3. 프로젝트 구조 계획

```text
04_mini_project/
├─ app/
│  ├─ core/
│  │  ├─ api_response.py       # 공통 API 응답 모델
│  │  └─ supabase_client.py    # 환경변수 로드 및 Supabase 연결
│  ├─ routers/
│  │  └─ user_router.py        # HTTP 요청, 상태 코드, 응답 처리
│  ├─ schemas/
│  │  └─ user_schema.py        # 요청 및 응답 데이터 검증
│  ├─ services/
│  │  └─ user_service.py       # Supabase User CRUD 처리
│  └─ jso.py                   # 담당자 로컬 실행용 앱
├─ sql/
│  └─ user.sql                 # users 테이블과 개발용 샘플 데이터
├─ tests/
│  └─ test_user_router.py      # mock 기반 Router 테스트
├─ .env.example                # 실제 키가 없는 환경변수 예시
├─ .gitignore
├─ requirements.txt
└─ pre_plan.md
```

### 3.1 계층별 책임

#### Router

- HTTP Method와 경로를 선언한다.
- 요청 Schema를 받는다.
- Service 함수를 호출한다.
- HTTP 상태 코드와 공통 응답을 반환한다.
- Service 예외를 404, 409, 500 응답으로 변환한다.
- Supabase 쿼리를 직접 작성하지 않는다.

#### Service

- Supabase 쿼리를 실행한다.
- 비밀번호를 해시한다.
- 회원 ID를 생성한다.
- DB 결과를 Pydantic 공개 모델로 변환한다.
- DB 내부 예외를 서비스 전용 예외로 변환한다.
- HTTPException을 직접 사용하지 않는다.

#### Schema

- 필수값과 최대 길이를 검증한다.
- 이메일을 소문자로 정규화한다.
- 이메일 형식을 검증한다.
- 비밀번호 최소 길이를 검증한다.
- 이름 앞뒤 공백을 제거한다.
- 공개 응답에서 비밀번호를 제외한다.

#### Core

- Supabase 연결 방식을 한 곳에서 관리한다.
- 공통 응답 형식을 제공한다.
- 실제 환경변수 값을 출력하지 않는다.

## 4. 명명 규칙

### 4.1 파일명

- 모두 소문자 snake_case를 사용한다.
- Router: `{기능명}_router.py`
- Service: `{기능명}_service.py`
- Schema: `{기능명}_schema.py`
- Test: `test_{기능명}_router.py`

### 4.2 Python 명명

- 클래스: PascalCase
- 함수: snake_case
- 변수: snake_case
- 상수: UPPER_SNAKE_CASE
- 내부 전용 함수: `_`로 시작

### 4.3 권장 함수명

```text
Router
- create_user
- get_users
- get_user
- update_user
- delete_user

Service
- user_create
- user_get_all
- user_get
- user_update
- user_delete
```

기존 프로젝트 규칙과 통합할 때는 팀의 공통 명명 규칙을 우선한다.

## 5. 데이터 모델 계획

### 5.1 users 테이블

| 컬럼 | PostgreSQL 타입 | 필수 | 제약조건 | 설명 |
|---|---|---:|---|---|
| user_id | text | Y | PK, 17자리 숫자 | 생성 시각 기반 회원 ID |
| email | text | Y | UNIQUE | 정규화된 이메일 |
| password | text | Y | NOT NULL | PBKDF2-SHA256 해시 |
| name | text | Y | NOT NULL | 회원 이름 |
| created_at | timestamptz | Y | DEFAULT now() | 생성 시각 |
| updated_at | timestamptz | Y | DEFAULT now() | 마지막 수정 시각 |

### 5.2 회원 ID 규칙

- 타입: 문자열
- 길이: 17자리
- 형식: `YYYYMMDDHHMMSSmmm`
- 예시: `20260723103045123`
- 기준 시간대: Asia/Seoul
- 생성 위치: Service 계층

밀리초까지만 사용하면 같은 밀리초에 두 요청이 들어올 때 충돌할 수 있다. 기본 구현 이후 다음 보완 방법을 검토한다.

1. 기본키 충돌 시 다음 밀리초까지 기다린 후 재시도
2. 애플리케이션 내부에서 마지막 생성 ID와 비교
3. DB 함수 또는 별도 sequence 사용
4. 요구사항 변경이 가능하면 난수 또는 UUID 결합

### 5.3 이메일 규칙

- 필수 입력
- 앞뒤 공백 제거
- 소문자로 저장
- 최대 254자
- `example@example.com` 형식 검증
- DB UNIQUE 제약조건 적용
- 애플리케이션의 사전 중복 검사와 DB 제약조건을 함께 사용

### 5.4 비밀번호 규칙

- 필수 입력
- 최소 8자
- 최대 128자
- API 응답에 포함하지 않음
- 로그에 기록하지 않음
- SQL 샘플 데이터에도 평문을 기록하지 않음
- PBKDF2-HMAC-SHA256 사용
- 무작위 16바이트 salt 사용
- 반복 횟수 600,000회

### 5.5 이름 규칙

- 필수 입력
- 앞뒤 공백 제거
- 공백만 입력할 수 없음
- 최대 100자

## 6. Pydantic Schema 계획

### 6.1 UserCreate

```python
class UserCreate(BaseModel):
    email: str
    password: str
    name: str
```

검증 항목:

- 이메일 형식과 최대 길이
- 이메일 소문자 정규화
- 비밀번호 8~128자
- 이름 1~100자
- 이름 공백 입력 방지

### 6.2 UserUpdate

현재 API는 PUT 전체 수정이므로 `UserCreate`와 같은 필드를 필수로 받는다.

```python
class UserUpdate(UserCreate):
    pass
```

일부 필드 수정이 필요해지면 PATCH API와 별도 Schema를 추가한다.

```python
class UserPatch(BaseModel):
    email: str | None = None
    password: str | None = None
    name: str | None = None
```

### 6.3 UserPublic

```python
class UserPublic(BaseModel):
    user_id: str
    email: str
    name: str
    created_at: datetime
    updated_at: datetime
```

`password` 필드는 절대 포함하지 않는다.

## 7. API 설계

### 7.1 공통 성공 응답

```json
{
  "success": true,
  "message": "처리 결과 안내 문구",
  "data": {}
}
```

### 7.2 회원 생성

- Method: POST
- Path: `/users`
- 성공 상태: 201 Created

요청:

```json
{
  "email": "user@example.com",
  "password": "safe-password",
  "name": "장상옥"
}
```

성공 응답:

```json
{
  "success": true,
  "message": "회원이 생성되었습니다.",
  "data": {
    "user_id": "20260723103045123",
    "email": "user@example.com",
    "name": "장상옥",
    "created_at": "2026-07-23T10:30:45.123+09:00",
    "updated_at": "2026-07-23T10:30:45.123+09:00"
  }
}
```

실패:

- 이메일 중복: 409
- 입력값 오류: 422
- DB 처리 실패: 500

### 7.3 회원 전체 조회

- Method: GET
- Path: `/users`
- 성공 상태: 200 OK
- 비밀번호를 제외한 회원 배열 반환

### 7.4 회원 단일 조회

- Method: GET
- Path: `/users/{user_id}`
- 성공 상태: 200 OK
- 미존재 회원: 404

### 7.5 회원 수정

- Method: PUT
- Path: `/users/{user_id}`
- 성공 상태: 200 OK
- 미존재 회원: 404
- 다른 회원과 이메일 중복: 409
- 입력값 오류: 422

PUT은 전체 수정이므로 이메일, 비밀번호, 이름을 모두 입력한다. 비밀번호가 전달되면 새 salt로 다시 해시한다.

### 7.6 회원 삭제

- Method: DELETE
- Path: `/users/{user_id}`
- 성공 상태: 200 OK
- 미존재 회원: 404
- 삭제된 공개 회원 정보를 반환

## 8. 예외 처리 계획

| 상황 | Service 처리 | HTTP 상태 | 사용자 메시지 |
|---|---|---:|---|
| 잘못된 요청 | Pydantic 검증 | 422 | 필드별 검증 메시지 |
| 회원 없음 | `None` 반환 | 404 | 회원을 찾을 수 없습니다. |
| 이메일 중복 | `DuplicateEmailError` | 409 | 이미 사용 중인 이메일입니다. |
| DB unique violation | 중복 예외로 변환 | 409 | 이미 사용 중인 이메일입니다. |
| 기타 DB 오류 | `UserServiceError` | 500 | 회원 정보를 처리하는 중 오류가 발생했습니다. |
| 환경변수 누락 | RuntimeError 후 서버 로그 | 500 | 내부 설정 오류 |

내부 DB 오류 문자열, URL, API 키, SQL 쿼리 전문은 사용자 응답에 포함하지 않는다. 운영 로그에는 비밀번호와 키를 제외한 오류 종류와 요청 식별 정보만 기록한다.

## 9. 공통 모듈 계획

### 9.1 Supabase Client

필요한 환경변수:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
```

원칙:

- 실제 값은 `.env`에만 입력한다.
- `.env`는 Git에서 제외한다.
- `.env.example`에는 placeholder만 기록한다.
- 일반 CRUD에서 Service Role Key 사용 여부는 팀의 RLS 정책에 따라 결정한다.
- Service Role Key는 브라우저나 프론트엔드에 전달하지 않는다.
- 키와 URL을 로그로 출력하지 않는다.

### 9.2 ApiResponse

기본 구조:

```python
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Any | None = None
```

향후 개선 시 Generic을 적용한다.

```python
T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T | None = None
```

## 10. Supabase SQL

### 10.1 실행 전 주의사항

1. 아래 SQL은 Supabase SQL Editor에서 실행한다.
2. 먼저 개발 또는 테스트 프로젝트에서 검증한다.
3. 운영 테이블이 이미 있으면 백업 후 실행한다.
4. Service Role Key와 실제 비밀번호는 SQL에 넣지 않는다.
5. 샘플 데이터는 개발 환경에서만 사용한다.
6. 샘플 데이터의 비밀번호 컬럼에는 PBKDF2 해시만 저장한다.

### 10.2 신규 테이블 생성 SQL

```sql
begin;

create table if not exists public.users (
    user_id text primary key,
    email text not null,
    password text not null,
    name text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    constraint users_user_id_format_check
        check (user_id ~ '^[0-9]{17}$'),
    constraint users_email_length_check
        check (char_length(email) between 3 and 254),
    constraint users_email_lowercase_check
        check (email = lower(email)),
    constraint users_email_format_check
        check (email ~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'),
    constraint users_password_not_empty_check
        check (char_length(password) > 0),
    constraint users_name_length_check
        check (char_length(btrim(name)) between 1 and 100)
);

create unique index if not exists users_email_unique_idx
    on public.users (lower(email));

comment on table public.users is '서비스 회원 정보를 저장하는 테이블';
comment on column public.users.user_id is 'YYYYMMDDHHMMSSmmm 형식의 17자리 문자열 ID';
comment on column public.users.email is '소문자로 정규화된 고유 이메일';
comment on column public.users.password is '평문이 아닌 PBKDF2-SHA256 해시';
comment on column public.users.name is '회원 표시 이름';
comment on column public.users.created_at is '회원 생성 시각';
comment on column public.users.updated_at is '마지막 수정 시각';

commit;
```

### 10.3 updated_at 자동 변경 함수 및 트리거

```sql
create or replace function public.set_users_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists users_set_updated_at on public.users;

create trigger users_set_updated_at
before update on public.users
for each row
execute function public.set_users_updated_at();
```

### 10.4 기존 bigint ID 테이블 마이그레이션

기존 `users.user_id`가 identity bigint일 때만 사용한다. 실행 전 백업이 필요하다.

```sql
begin;

alter table public.users
    alter column user_id drop identity if exists;

alter table public.users
    alter column user_id type text
    using user_id::text;

commit;
```

기존 숫자 ID가 17자리가 아니라면 `users_user_id_format_check`를 바로 추가할 수 없다. 먼저 다음 쿼리로 확인한다.

```sql
select user_id
from public.users
where user_id !~ '^[0-9]{17}$';
```

조회 결과가 있으면 데이터 변환 방식을 팀과 합의한 후 제약조건을 추가한다.

### 10.5 RLS 계획

현재 백엔드가 Service Role Key를 사용한다면 RLS를 우회할 수 있다. 향후 Anon Key와 인증된 사용자 토큰을 사용할 경우 다음처럼 RLS를 활성화하고 정책을 별도로 설계한다.

```sql
alter table public.users enable row level security;
```

User CRUD가 인증 시스템과 연결되기 전에는 임의의 공개 정책을 만들지 않는다. 특히 모든 사용자가 전체 회원의 이메일을 조회하거나 삭제할 수 있는 정책은 만들지 않는다.

## 11. 개발용 샘플 데이터 입력 SQL

### 11.1 샘플 데이터 원칙

- 개발 또는 테스트 Supabase에서만 실행한다.
- 실제 사람의 이메일과 이름을 사용하지 않는다.
- 평문 비밀번호를 SQL에 기록하지 않는다.
- 동일 SQL을 여러 번 실행해도 중복 오류가 발생하지 않도록 한다.
- 운영 배포 전 샘플 데이터를 제거한다.

### 11.2 샘플 회원 10명 입력

아래 해시는 개발용 임시 해시이며 실제 비밀번호를 표현하지 않는다.

```sql
insert into public.users (user_id, email, password, name)
values
    (
        '20260723090000001',
        'sample-user-01@example.com',
        'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=',
        '샘플회원01'
    ),
    (
        '20260723090000002',
        'sample-user-02@example.com',
        'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=',
        '샘플회원02'
    ),
    (
        '20260723090000003',
        'sample-user-03@example.com',
        'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=',
        '샘플회원03'
    ),
    (
        '20260723090000004',
        'sample-user-04@example.com',
        'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=',
        '샘플회원04'
    ),
    (
        '20260723090000005',
        'sample-user-05@example.com',
        'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=',
        '샘플회원05'
    ),
    (
        '20260723090000006',
        'sample-user-06@example.com',
        'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=',
        '샘플회원06'
    ),
    (
        '20260723090000007',
        'sample-user-07@example.com',
        'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=',
        '샘플회원07'
    ),
    (
        '20260723090000008',
        'sample-user-08@example.com',
        'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=',
        '샘플회원08'
    ),
    (
        '20260723090000009',
        'sample-user-09@example.com',
        'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=',
        '샘플회원09'
    ),
    (
        '20260723090000010',
        'sample-user-10@example.com',
        'pbkdf2_sha256$600000$4raNjbxK9dGMvwIVYYgTog==$P7zvKA+cTEGhZnk3h9Dzj4ev/TCM0CuBc5bZDn6sUfE=',
        '샘플회원10'
    )
on conflict do nothing;
```

### 11.3 샘플 데이터 입력 확인

비밀번호는 조회하지 않는다.

```sql
select
    user_id,
    email,
    name,
    created_at,
    updated_at
from public.users
where email like 'sample-user-%@example.com'
order by user_id;
```

예상 결과:

- 총 10건
- 모든 ID가 17자리 숫자 문자열
- 이메일이 모두 고유함
- `created_at`, `updated_at`이 자동 입력됨

건수만 확인하려면 다음 SQL을 실행한다.

```sql
select count(*) as sample_user_count
from public.users
where email like 'sample-user-%@example.com';
```

### 11.4 샘플 데이터 수정 테스트

```sql
update public.users
set name = '수정된샘플회원01'
where email = 'sample-user-01@example.com';

select user_id, email, name, created_at, updated_at
from public.users
where email = 'sample-user-01@example.com';
```

확인 항목:

- 이름이 변경되었는지 확인한다.
- `updated_at`이 기존 값보다 이후인지 확인한다.

### 11.5 샘플 데이터 삭제

개발 검증이 끝나면 다음 SQL로 샘플 회원만 삭제한다.

```sql
delete from public.users
where email like 'sample-user-%@example.com';
```

삭제 확인:

```sql
select count(*) as remaining_sample_user_count
from public.users
where email like 'sample-user-%@example.com';
```

예상 결과는 `0`이다.

### 11.6 전체 테이블 삭제 SQL

다음 SQL은 테이블과 데이터가 모두 삭제되므로 개발용 프로젝트를 초기화할 때만 사용한다.

```sql
drop table if exists public.users cascade;
drop function if exists public.set_users_updated_at();
```

운영 환경에서는 실행하지 않는다.

## 12. 구현 순서

### 1단계: 프로젝트 및 환경 확인

1. Python 버전을 확인한다.
2. 가상환경을 생성하고 활성화한다.
3. `requirements.txt`를 설치한다.
4. `.gitignore`에 `.env`가 포함되어 있는지 확인한다.
5. `.env.example`에 실제 키가 없는지 확인한다.
6. Supabase 프로젝트와 `users` 테이블 존재 여부를 확인한다.

### 2단계: 데이터베이스 준비

1. Supabase SQL Editor에서 테이블 생성 SQL을 실행한다.
2. `user_id`, `email`, `password`, `name`, 시간 컬럼을 확인한다.
3. unique index와 CHECK 제약조건을 확인한다.
4. updated_at 트리거를 생성한다.
5. 개발 환경에서만 샘플 회원을 입력한다.
6. 샘플 데이터 조회와 수정으로 트리거를 확인한다.

### 3단계: 공통 모듈 확인

1. `get_required_env()`로 필수 환경변수를 검증한다.
2. `get_supabase()`가 공통 연결을 생성하는지 확인한다.
3. `ApiResponse` 필드 구조를 확인한다.
4. 키 또는 DB 오류가 사용자 응답에 노출되지 않도록 한다.

### 4단계: Schema 구현

1. `UserCreate`를 작성한다.
2. 이메일 정규화와 검증을 작성한다.
3. 비밀번호 길이 검증을 작성한다.
4. 이름 공백 및 길이 검증을 작성한다.
5. `UserUpdate`를 작성한다.
6. 비밀번호가 없는 `UserPublic`을 작성한다.
7. Swagger 설명과 예시를 추가한다.

### 5단계: Service 구현

1. ID 생성 함수를 작성한다.
2. 비밀번호 해시 함수를 작성한다.
3. DB dict를 `UserPublic`으로 변환한다.
4. 이메일 중복 확인 함수를 작성한다.
5. 생성, 전체 조회, 단일 조회, 수정, 삭제 함수를 작성한다.
6. DB 예외를 서비스 전용 예외로 변환한다.
7. DB unique violation을 중복 이메일 예외로 구분한다.

### 6단계: Router 구현

1. `/users` prefix를 지정한다.
2. POST, GET, PUT, DELETE 경로를 작성한다.
3. 201, 200, 404, 409, 422, 500 상태를 구분한다.
4. 공통 응답을 적용한다.
5. Router에서 Supabase를 직접 호출하지 않는지 확인한다.

### 7단계: 실행 앱 연결

1. 담당자 로컬 앱에 User Router를 등록한다.
2. 팀 공용 앱에는 팀장과 협의 후 User Router를 등록한다.
3. `/docs`에서 5개 User API가 보이는지 확인한다.

### 8단계: 테스트

1. mock 기반 Router 테스트를 실행한다.
2. 실제 Supabase에서는 고유 이메일의 임시 회원만 사용한다.
3. 실제 연동 테스트 후 생성한 ID만 삭제한다.
4. 테스트 데이터가 0건 남았는지 확인한다.
5. 전체 pytest를 실행한다.

### 9단계: Git 및 PR

1. `.env`, 개인 실행 파일, 팀 규칙상 제외 테스트를 Stage하지 않는다.
2. User CRUD 관련 파일만 Stage한다.
3. 변경 파일 목록과 diff를 확인한다.
4. 개인 브랜치에 커밋한다.
5. 원격 개인 브랜치에 push한다.
6. 팀에서 지정한 base 브랜치로 Pull Request를 생성한다.
7. PR의 Files changed에 불필요한 문서나 비밀 파일이 없는지 확인한다.

## 13. 테스트 계획

### 13.1 Router 단위 테스트

| 번호 | 테스트 | 예상 결과 |
|---:|---|---|
| 1 | 정상 회원 생성 | 201 |
| 2 | 전체 회원 조회 | 200, 배열 |
| 3 | 단일 회원 조회 | 200, 객체 |
| 4 | 정상 회원 수정 | 200 |
| 5 | 정상 회원 삭제 | 200 |
| 6 | 없는 회원 조회 | 404 |
| 7 | 없는 회원 수정 | 404 |
| 8 | 없는 회원 삭제 | 404 |
| 9 | 필수 필드 누락 | 422 |
| 10 | 잘못된 이메일 | 422 |
| 11 | 8자 미만 비밀번호 | 422 |
| 12 | 중복 이메일 | 409 |
| 13 | 공개 응답 필드 확인 | password 없음 |
| 14 | DB 내부 오류 | 안전한 500 메시지 |

### 13.2 Service 단위 테스트

- ID가 17자리 숫자 문자열인지 확인
- 비밀번호 해시가 원문과 다른지 확인
- 같은 비밀번호도 salt로 인해 다른 해시가 생성되는지 확인
- 공개 모델에 비밀번호가 없는지 확인
- Supabase 빈 결과가 `None`으로 변환되는지 확인
- Supabase 예외가 `UserServiceError`로 변환되는지 확인
- DB 이메일 중복 오류가 `DuplicateEmailError`로 변환되는지 확인

### 13.3 실제 Supabase 통합 테스트

1. UUID를 이용해 고유 테스트 이메일을 만든다.
2. POST로 임시 회원을 생성한다.
3. 응답 ID가 17자리 문자열인지 확인한다.
4. 전체 조회 목록에 해당 ID가 있는지 확인한다.
5. 단일 조회 결과를 확인한다.
6. 이름과 이메일을 수정한다.
7. 수정된 `updated_at`을 확인한다.
8. 회원을 삭제한다.
9. 삭제 후 단일 조회가 404인지 확인한다.
10. `finally`에서 테스트 ID를 다시 정리한다.

실제 운영 회원을 수정하거나 삭제하지 않는다.

## 14. 실행 방법

### 14.1 가상환경 생성 및 활성화

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 14.2 패키지 설치

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 14.3 개인 개발 서버 실행

```powershell
uvicorn app.jso:app --reload
```

확인 주소:

- API 문서: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

### 14.4 테스트 실행

```powershell
python -m pytest tests/test_user_router.py -q
```

전체 테스트:

```powershell
python -m pytest -q
```

## 15. 보안 점검표

- [ ] `.env`가 `.gitignore`에 포함되어 있다.
- [ ] `.env.example`에 placeholder만 있다.
- [ ] 실제 Gemini 또는 Supabase 키가 코드에 없다.
- [ ] Service Role Key가 로그에 출력되지 않는다.
- [ ] API 응답에 password가 없다.
- [ ] SQL 샘플 데이터에 평문 비밀번호가 없다.
- [ ] 테스트에 실제 운영 키가 없다.
- [ ] DB 오류 전문이 사용자 응답에 없다.
- [ ] 샘플 회원은 운영 배포 전에 제거했다.
- [ ] PR Files changed에서 비밀 파일을 다시 확인했다.

## 16. 코드 품질 점검표

- [ ] Python 3.12.7에서 실행된다.
- [ ] Router, Service, Schema 책임이 분리되어 있다.
- [ ] 인자와 반환 타입이 일관된다.
- [ ] `user_id`가 모든 계층에서 `str`이다.
- [ ] 공개 함수에 짧고 정확한 docstring이 있다.
- [ ] 초보자가 이해할 수 있는 필요한 주석만 있다.
- [ ] 사용하지 않는 import가 없다.
- [ ] 동일한 오류 처리 코드가 지나치게 반복되지 않는다.
- [ ] pytest가 모두 통과한다.
- [ ] Swagger에서 요청 조건을 확인할 수 있다.

## 17. 예상 위험과 대응

| 위험 | 영향 | 대응 |
|---|---|---|
| 동일 밀리초 ID 충돌 | 생성 요청 500 | 충돌 재시도 또는 ID 정책 개선 |
| 동시 중복 가입 | DB unique violation | DB 오류를 409로 변환 |
| Service Role Key 노출 | 전체 DB 권한 위험 | `.env` 관리, 키 재발급, RLS 검토 |
| 응답에 비밀번호 포함 | 개인정보 유출 | 공개 Schema 고정 및 테스트 |
| 개인 실행 파일 Git 제외 | 원격 서버 실행 불가 | 공용 앱에 Router 등록 확인 |
| 샘플 데이터 운영 반영 | 불필요한 계정 생성 | seed SQL 분리 및 배포 전 삭제 |
| PUT 시 비밀번호 재입력 | 사용성 저하 | 향후 PATCH API 검토 |
| 모든 DB 오류가 500 | 원인 구분 어려움 | 오류 코드별 서비스 예외 정의 |

## 18. Git 반영 대상

기본 반영 파일:

```text
app/routers/user_router.py
app/services/user_service.py
app/schemas/user_schema.py
sql/user.sql
```

팀 협의 후 반영 파일:

```text
app/core/api_response.py
app/core/supabase_client.py
app/main.py 또는 팀 공용 실행 파일
tests/test_user_router.py
.gitignore
.env.example
```

반영 금지 파일:

```text
.env
app/jso.py               # 팀 규칙상 개인 실행 파일일 때
실제 키가 포함된 파일
__pycache__/
*.pyc
.pytest_cache/
```

## 19. 최종 인수 조건

다음 항목을 모두 만족하면 User CRUD 담당 작업이 완료된 것으로 판단한다.

1. User API 5개가 Swagger에 표시된다.
2. 모든 정상 CRUD 요청이 예상 상태 코드를 반환한다.
3. 미존재 회원은 404를 반환한다.
4. 중복 이메일은 애플리케이션과 DB 양쪽에서 차단된다.
5. 비밀번호는 PBKDF2 해시로 저장된다.
6. 모든 공개 응답에 비밀번호가 없다.
7. `updated_at`이 수정 시 자동 변경된다.
8. pytest가 모두 통과한다.
9. 실제 Supabase 임시 CRUD 테스트가 통과한다.
10. 실제 연동 테스트 데이터가 남지 않는다.
11. `.env`와 비밀키가 Git에 포함되지 않는다.
12. 병합 대상 브랜치의 공용 앱에 User Router가 등록된다.
13. 팀 리뷰에서 코드 구조와 명명 규칙을 승인받는다.

## 20. 향후 확장 계획

User CRUD 완료 후 다음 기능을 단계적으로 검토할 수 있다.

1. 로그인 및 비밀번호 검증 함수
2. Supabase Auth 연동
3. JWT 기반 인증
4. 본인 정보만 수정 및 삭제할 수 있는 권한 검사
5. 이메일 인증
6. 비밀번호 변경 및 재설정
7. PATCH 부분 수정 API
8. 페이지네이션과 정렬
9. 회원 검색
10. 감사 로그와 보안 로그
11. ID 생성 정책 개선
12. Generic 공통 응답 적용
13. 테스트용 Supabase 프로젝트 분리
14. CI에서 pytest 자동 실행

