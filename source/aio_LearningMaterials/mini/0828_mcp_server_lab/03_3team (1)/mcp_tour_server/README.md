# Tour MCP Server

PostgreSQL에서 호텔과 관광지 데이터를 조회하는 Streamable HTTP 기반 MCP 서버입니다.
서버는 `hotel`, `spot` 두 Tool을 제공합니다.

- Endpoint: `http://127.0.0.1:8033/mcp`
- Transport: `streamable-http`
- Database: PostgreSQL

## 디렉터리 구조

```text
mcp_tour_server/
├─ app/
│  ├─ main.py                    # MCP 서버 생성 및 Tool 등록
│  └─ tools/
│     ├─ hotel_tool.py           # hotel Tool 등록
│     └─ spot_tool.py            # spot Tool 등록
├─ domains/
│  ├─ hotel/
│  │  ├─ service.py              # 입력 검증·응답 조립
│  │  ├─ repository.py           # hotels 조회 SQL
│  │  └─ schemas.py              # Hotel 입출력 모델
│  └─ spot/
│     ├─ service.py              # 입력 검증·응답 조립
│     ├─ repository.py           # spots 조회 SQL
│     └─ schemas.py              # Spot 입출력 모델
├─ infrastructure/
│  └─ database/
│     └─ connection.py           # PostgreSQL 연결 풀
├─ db/
│  ├─ init/
│  │  ├─ 01_hotel_tables.sql
│  │  └─ 02_spot_tables.sql
│  └─ seed/
│     ├─ 01_hotel_data.sql
│     └─ 02_spot_data.sql
├─ .env.example
├─ docker-compose.yml
└─ requirements.txt
```

현재는 디렉터리 뼈대만 생성된 상태입니다. 기존 프로젝트의 코드는 변경하지 않았으므로,
파일을 옮길 때 import 경로를 이 구조에 맞게 함께 조정해야 합니다.

## Tool 계약

### `hotel`

부산 호텔을 1박 최대 가격으로 검색합니다.

```json
{
  "city": "부산",
  "max_price": 150000
}
```

`city`는 현재 부산만 지원하고, `max_price`는 1 이상이어야 합니다.

```json
{
  "items": [
    {
      "hotel_id": 1,
      "name": "해운대 오션 스테이",
      "city": "부산",
      "district": "해운대구",
      "price": 89000,
      "near_spot": "해운대해수욕장"
    }
  ],
  "count": 1,
  "source": "postgresql"
}
```

### `spot`

부산 또는 서울의 관광지를 검색합니다.

```json
{
  "city": "서울"
}
```

```json
{
  "items": [
    {
      "spot_id": 1,
      "name": "경복궁",
      "city": "서울",
      "district": "종로구",
      "category": "궁궐",
      "description": "조선 시대의 대표 궁궐"
    }
  ],
  "count": 1,
  "source": "postgresql"
}
```

## 환경 설정

`.env.example`을 복사하여 `.env`를 만들고, 실제 환경에 맞게 값을 변경합니다.

```powershell
Copy-Item .env.example .env
```

`.env`에는 비밀번호가 포함될 수 있으므로 Git에 커밋하지 않습니다.

```env
TOUR_MCP_HOST=0.0.0.0
TOUR_MCP_PORT=8033
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=travel_mcp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

## DB 실행

`docker-compose.yml`과 SQL 파일을 이 폴더로 옮긴 뒤 PostgreSQL을 실행합니다.

```powershell
docker compose up -d postgres
```

`db/init/`은 테이블과 인덱스를 만들고, `db/seed/`는 개발용 초기 데이터를 넣습니다.
SQL 파일의 숫자 접두사는 Docker 초기화 순서를 고정합니다.

## 서버 실행

의존성을 설치한 뒤 `app/main.py`를 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\app\main.py
```

서버가 실행되면 MCP 클라이언트는 `http://127.0.0.1:8033/mcp`로 연결합니다.

## 개발 분리 원칙

도메인별 파일은 서로 독립적으로 수정합니다.

| 담당 | 수정 범위 |
| --- | --- |
| Hotel | `domains/hotel/`, `app/tools/hotel_tool.py`, `db/init/01_hotel_tables.sql`, `db/seed/01_hotel_data.sql` |
| Spot | `domains/spot/`, `app/tools/spot_tool.py`, `db/init/02_spot_tables.sql`, `db/seed/02_spot_data.sql` |
| 통합 | `app/main.py`, `infrastructure/database/connection.py`, `.env.example`, `docker-compose.yml`, `requirements.txt`, `README.md` |

Tool은 `app/tools/`에서 MCP 객체에 등록만 하고, 입력 검증과 응답 조립은
`domains/*/service.py`, SQL 조회는 `domains/*/repository.py`에서 담당합니다.
