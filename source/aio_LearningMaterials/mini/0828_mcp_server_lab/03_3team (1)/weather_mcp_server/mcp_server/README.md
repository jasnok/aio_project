# Weather Comparison MCP Server

서울·부산의 현재 날씨와 향후 7일 예보를 Open-Meteo와 기상청 데이터로 비교하는
Streamable HTTP MCP Server입니다.

## 제공 Tool

| Tool | 설명 |
| --- | --- |
| `compare_current_weather(city)` | Open-Meteo Current와 기상청 초단기실황 비교 |
| `compare_weekly_forecast(city, days=7)` | Open-Meteo 일별예보와 기상청 단기·중기예보 비교 |

지원 도시는 `서울`, `부산`이며 `days`는 1~7입니다.

## 데이터 구성

```text
현재 날씨
├─ Open-Meteo Current
└─ 기상청 초단기실황

향후 7일
├─ Open-Meteo Daily: 7일
└─ 기상청
   ├─ 단기예보: 글피까지의 시간별 예보를 일별 집계
   └─ 중기예보: 이후 날짜의 오전·오후 예보와 최저·최고기온
```

두 공급자의 응답은 공통 모델로 변환됩니다. 수치 차이는
`Open-Meteo - 기상청` 기준입니다. 한 공급자나 기상청 중기예보가 실패하면 다른
결과를 유지하고 `status=partial`과 `errors`를 반환합니다.

## 디렉터리

```text
mcp_server/
├── 03_weather_mcp_server.py
├── .env.example
├── requirements.txt
├── client/
│   ├── connection.py
│   ├── open_meteo_client.py
│   └── kma_client.py
├── core/weather/
│   ├── exceptions.py
│   ├── locations.py
│   ├── mappings.py
│   ├── schemas.py
│   ├── normalizer.py
│   ├── comparator.py
│   └── service.py
└── tests/test_weather.py
```

## 기상청 API 신청

공공데이터포털에서 다음 두 API를 모두 활용신청해야 7일 전체 비교가 가능합니다.

1. [기상청 단기예보 조회서비스](https://www.data.go.kr/data/15084084/openapi.do)
2. [기상청 중기예보 조회서비스](https://www.data.go.kr/data/15059468/openapi.do)

단기예보만 승인된 키에서는 현재 날씨와 글피까지는 비교되지만 이후 날짜는
Open-Meteo만 반환되어 `partial` 상태가 됩니다.

## 설치

`mcp_server` 폴더만 받은 경우 해당 폴더에서 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env`에 공공데이터포털의 Decoding 인증키를 입력합니다.

```env
KMA_SERVICE_KEY=발급받은_Decoding_인증키
MCP_HOST=127.0.0.1
MCP_PORT=8010
```

인증키는 Git에 Commit하거나 로그·스크린샷에 노출하지 않습니다.

## 실행

`mcp_server` 폴더에서:

```powershell
python .\03_weather_mcp_server.py
```

프로젝트 루트에서:

```powershell
python .\mcp_server\03_weather_mcp_server.py
```

MCP endpoint는 `http://127.0.0.1:8010/mcp`입니다.

## 테스트

프로젝트 루트에서:

```powershell
python -m unittest discover -s mcp_server\tests -v
```

`mcp_server` 폴더에서:

```powershell
python -m unittest discover -s tests -v
```

## 응답 상태

- `complete`: 요청한 모든 날짜에서 두 공급자를 비교함
- `partial`: 한 공급자가 일부 또는 전체 날짜를 제공하지 못함
- `error`: 두 공급자 모두 결과를 제공하지 못함

오류 메시지에는 인증키나 인증키가 포함된 요청 URL을 출력하지 않습니다.
