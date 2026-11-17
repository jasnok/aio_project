# 날씨 MCP Server 계획서

## 1. 목표

도시 또는 위치를 입력받아 현재 날씨와 예보를 제공한다. 현재 구현된 Open-Meteo 연동을 유지하면서, 공공데이터포털의 `기상청_단기예보 조회서비스`를 추가 공급자로 사용할 수 있도록 외부 API 의존성을 분리한다.

### 이번 구현 범위

1. 기존 `get_current_weather`, `get_weather_forecast`의 동작을 유지한다.
2. 기상청 Provider와 `compare_weather_sources` Tool을 추가한다.
3. 기능별 MCP 파일과 모델·서비스 모듈을 분리한다.
4. 특보·대기질·주소 변환 Tool과 실제 날씨 Resource·Prompt는 이번 구현에서 만들지 않는다.

### 현재 구현 상태

| 기능 | 상태 | 현재 동작 |
|---|---|---|
| 현재 날씨 | 구현 | `WEATHER_PROVIDER`에 따라 Open-Meteo 또는 KMA 실황 조회 |
| 예보 | 구현 | `WEATHER_PROVIDER`에 따라 Open-Meteo 또는 KMA 단기예보 조회 |
| 공급자 비교 | 구현 | KMA·Open-Meteo 예보를 병렬 조회하고 일별 최고기온 차이 계산 |
| 예보 버전 조회 | Client 구현 | `KmaClient` 메서드만 구현, MCP Tool·자동 갱신 정책은 미구현 |
| Resource·Prompt | 등록 지점만 구현 | 실제 Resource·Prompt 없음 |

## 2. 기상청 API 명세

- 서비스명: 기상청_단기예보 조회서비스
- Base endpoint: `https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0`
- 응답 형식: JSON 우선 지원, 필요하면 XML도 파싱 가능하도록 client를 분리한다.
- 공통 인증: 공공데이터포털에서 발급받은 `serviceKey`
- 공통 조회 조건: `base_date`, `base_time`, `nx`, `ny`

| 오퍼레이션 | 경로 | 용도 | 서비스 메서드 |
|---|---|---|---|
| 예보버전조회 | `/getFcstVersion` | 초단기실황·초단기예보·단기예보의 수정 예보 버전 확인 | `get_forecast_version()` |
| 단기예보조회 | `/getVilageFcst` | 발표일자·발표시각·예보 격자로 단기예보 조회 | `get_village_forecast()` |
| 초단기예보조회 | `/getUltraSrtFcst` | 발표일자·발표시각·예보 격자로 초단기예보 조회 | `get_ultra_short_forecast()` |
| 초단기실황조회 | `/getUltraSrtNcst` | 발표일자·발표시각·예보 격자로 실황 조회 | `get_ultra_short_observation()` |

기상청 원본 항목은 `category`, `fcstValue` 또는 `obsrValue`, `fcstDate`, `fcstTime`, `baseDate`, `baseTime`, `nx`, `ny`를 기준으로 파싱한다. 단기예보의 대표 category는 `TMP`, `PTY`, `SKY`, `REH`, `WSD`이며, 실제 제공 항목은 API 응답 fixture로 확정한다.

### 요청 파라미터 계약

| API | 필수 파라미터 | 기본값·규칙 |
|---|---|---|
| 공통 | `serviceKey`, `numOfRows`, `pageNo` | 충분한 `numOfRows`와 pagination을 지원한다. |
| 공통 | `dataType` | `JSON`을 기본값으로 사용한다. |
| 초단기실황 | `base_date`, `base_time`, `nx`, `ny` | 매시 정시 기준, API 제공 시각 이후의 최신 발표를 선택한다. |
| 초단기예보 | `base_date`, `base_time`, `nx`, `ny` | 매시 30분 기준, 생산 완료 시각 이후의 최신 발표를 선택한다. |
| 단기예보 | `base_date`, `base_time`, `nx`, `ny` | 02·05·08·11·14·17·20·23시 중 최신 발표를 선택한다. |
| 예보버전 | `ftype`, `basedatetime` | `ftype`: `ODAM`·`VSRT`·`SHRT`; `basedatetime`: `YYYYMMDDHHmm` |

`serviceKey`는 URL Encode된 인증키를 사용한다. `httpx` query parameter의 이중 인코딩 여부를 별도 테스트한다.

가이드 기준 운영 제약:

- 서비스는 남한 지역만 제공한다. 북한·해외 위치는 기상청 Provider의 지원 범위 오류로 처리하고, 해외는 Open-Meteo를 사용한다.
- 모든 발표·예보 시각은 KST(`Asia/Seoul`)로 계산하고 응답에는 ISO 8601 시각과 원본 `baseDate`·`baseTime`을 함께 보존한다.
- 초단기실황은 매시 정시에 생성되고 10분마다 갱신된다. API 호출은 해당 시각 10분 이후를 기본으로 한다.
- 초단기예보는 매시 30분에 생성되고 45분 이후 생산 완료된다. API 호출은 해당 시각 45분 이후를 기본으로 한다.
- 단기예보 발표 시각은 `0200`, `0500`, `0800`, `1100`, `1400`, `1700`, `2000`, `2300`이며 제공 시각은 발표 후 약 10분이다.
- 단기예보는 발표 시각에 따라 최대 5일까지 제공되며, 뒤쪽 예보 기간은 3시간 간격으로 제공될 수 있다. 응답의 실제 `fcstDate`·`fcstTime`을 기준으로 그룹화한다.

## 3. 제공할 MCP Tool

### `get_current_weather`

- 입력: `city` 또는 위치 정보
- 출력: 지역, 관측 시각, 기온, 습도, 풍속, 강수 상태, 데이터 출처
- 기상청 구현: `/getUltraSrtNcst`
- 조회 시각: 현재 시각 기준으로 사용 가능한 최신 발표 `base_date`·`base_time`을 계산한다.
- 실황 category: `T1H`, `RN1`, `UUU`, `VVV`, `REH`, `PTY`, `VEC`, `WSD`

### `get_weather_forecast`

- 입력: `city` 또는 위치 정보, 조회 일수
- 출력: 날짜별 최저·최고 기온, 하늘 상태, 강수 확률 또는 강수량
- 조회 일수는 공급자별 지원 범위 안에서 검증한다.
- 기상청 구현: `/getVilageFcst`; 필요한 경우 당일 초단기예보는 `/getUltraSrtFcst`를 사용한다.
- 단기예보 category: `POP`, `PTY`, `PCP`, `REH`, `SNO`, `SKY`, `TMP`, `TMN`, `TMX`, `UUU`, `VVV`, `WAV`, `VEC`, `WSD`

### `compare_weather_sources`

- 목적: 동일한 위치와 예보 기준 시각의 기상청·Open-Meteo 결과를 함께 조회한다.
- 입력: `city` 또는 `latitude`·`longitude`, 조회 일수, 선택적 기준 날짜
- 출력: 공급자별 예보 결과, 일별 최고기온 차이, 비교 시각, 데이터 출처, 공급자별 성공·실패 상태
- 기상청 구현: 실황 비교는 `/getUltraSrtNcst`, 예보 비교는 `/getVilageFcst`로 고정한다.
- 현재 비교 항목: 일별 `max_temperature_c` 차이. 강수·풍속·상태 차이 계산은 TODO다.
- 한 공급자만 실패하면 성공 결과와 실패 사유를 함께 반환하고, 둘 다 실패하면 Tool 오류를 반환한다.
- 비교 시 기상청 `TMP`·`RN1`·`POP`·`WSD`와 Open-Meteo의 동일 단위 필드를 사용한다. 기상청 `PCP`·`SNO`처럼 범주형 값은 수치 차이 계산에서 제외하거나 범주 일치 여부만 표시한다.

두 API는 예보 모델과 발표 시각이 다르므로 정확도 우열을 판정하지 않고 값의 차이와 데이터 기준을 표시한다.

현재 비교 결과의 실제 계약은 다음과 같다.

```json
{
  "city": "서울",
  "requested_at": "2026-08-28T12:00:00+09:00",
  "kma": {"status": "ok", "base_date": "20260828", "base_time": "1100", "items": []},
  "open_meteo": {"status": "ok", "items": []},
  "differences": [{"date": "2026-08-28", "max_temperature_c": 1.2}],
  "comparison_notes": ["PCP는 범주형 값이므로 수치 차이를 계산하지 않음"]
}
```

### 향후 추가 Tool(이번 범위 제외)

- `get_weather_alerts`: 기상 특보
- `get_air_quality`: 대기질 정보
- `resolve_location`: 주소·위도를 기상청 격자 좌표로 변환

## 4. 권장 내부 구조

```text
weather/
├── __init__.py
├── server.py                         # FastMCP 생성, 전체 기능 등록, transport 실행
├── config.py                         # 환경 변수 로드·검증 및 날씨 서버 설정
├── models/
│   ├── __init__.py                   # 외부 공개 모델과 schema 진입점
│   ├── requests.py                   # 날씨 Tool 입력 schema
│   ├── responses.py                  # MCP Tool 출력 schema
│   ├── weather.py                    # 날씨·예보 도메인 모델
│   ├── compare.py                    # 공급자별 값·차이·상태 모델
│   └── kma.py                        # 기상청 원본 응답 모델·category 구조
├── tools/
│   ├── __init__.py                   # 날씨 Tool 전체를 서버에 등록
│   ├── current.py                    # get_current_weather 입력 검증·응답 구성
│   ├── forecast.py                   # get_weather_forecast 입력 검증·응답 구성
│   ├── compare.py                    # compare_weather_sources 입력 검증·차이 응답 구성
│   └── alerts.py                     # get_weather_alerts 등록 예정
├── resources/
│   ├── __init__.py                   # 날씨 Resource 전체를 서버에 등록
│   └── __init__.py                   # 현재 실제 Resource 없음
├── prompts/
│   ├── __init__.py                   # 날씨 Prompt 전체를 서버에 등록
│   └── __init__.py                   # 현재 실제 Prompt 없음
└── services/
    ├── __init__.py                   # 서비스 공개 진입점
    ├── weather_service.py            # Provider 선택·비교·공통 업무 규칙
    ├── weather_provider.py           # 공급자 공통 인터페이스 정의
    ├── kma_client.py                 # 기상청 endpoint·공통 파라미터·HTTP 요청만 담당
    ├── kma_provider.py               # KMA client 호출·발표 시각 선택·응답 정규화
    ├── open_meteo_client.py          # Open-Meteo API HTTP 요청만 담당
    ├── weather_mapper.py             # 공급자 원본 응답을 내부 모델로 변환
    └── coordinate_converter.py       # 위경도와 기상청 nx·ny 변환
```

`tools/*.py`가 `kma_client.py`나 `kma_operations.py`를 직접 호출하지 않도록 하고, 다음 흐름을 유지한다.

```text
MCP Tool → WeatherService → WeatherProvider → KMA/Open-Meteo API
```

### 실제 등록·호출 연결

- `weather/server.py`: `WeatherService`를 생성하고 Tool·Resource·Prompt 등록 함수를 호출한다.
- `tools/current.py`, `tools/forecast.py`, `tools/compare.py`: MCP decorator, 입력 schema 연결, 서비스 호출, 공개 응답 구성을 담당한다.
- `services/weather_service.py`: `current()`, `forecast()`, `compare_sources()`를 제공한다.
- `services/weather_provider.py`: Provider가 구현해야 할 `current()`·`forecast()` Protocol을 정의한다.
- `services/kma_client.py`: HTTP GET, query parameter, timeout, JSON/XML 선택을 담당한다.
- `services/kma_provider.py`: `KmaClient`를 통해 실황·단기예보를 조회하고 KST 발표 시각을 선택한다.
- `services/weather_mapper.py`: 원본 응답을 `models/` 내부 모델로 변환한다.

의존 방향은 Tool → Service → Provider → Client → Mapper로 고정한다.

### 파일 역할 규칙

- `tools/*.py`: MCP에 노출되는 이름, 설명, 입력 schema, 오류 변환, 응답 형태를 정의한다. API 호출과 좌표 계산은 하지 않는다.
- `resources/*.py`: URI 기반의 읽기 전용 데이터를 제공한다. 변경 작업이나 무거운 검색은 Tool로 제공한다.
- `prompts/*.py`: 모델이 날씨 정보를 해석하거나 여행 계획에 활용할 수 있는 재사용 템플릿만 정의한다.
- `models/requests.py`: Tool 호출 파라미터와 범위·형식 검증을 정의한다.
- `models/responses.py`: MCP 클라이언트에 공개할 안정적인 응답 계약을 정의한다.
- `models/weather.py`: 공급자와 무관한 내부 날씨·예보 도메인 모델을 정의한다.
- `models/kma.py`: 기상청 응답의 `response.body.items.item` 목록을 추출하고 result code를 검사한다. Typed Pydantic 모델은 TODO다.
- `models/compare.py`: 두 공급자의 정규화 값, 항목별 차이, 부분 실패 상태를 정의한다.
- `services/*.py`: 외부 API 호출, Provider 선택, 변환 등 비즈니스 로직을 담당한다. 현재 retry·cache는 구현되지 않았다.
- `server.py`: 각 `__init__.py`의 등록 함수를 호출하고 서버를 실행한다.

## 5. 기상청 API 연동 계획

1. `KMA_BASE_URL`에 제공된 endpoint를 설정하고 `serviceKey`를 환경 변수로 주입한다.
2. `base_date`, `base_time`, `nx`, `ny`, `pageNo`, `numOfRows`, `dataType` 공통 파라미터를 client에서 관리한다.
3. `kma_client.py`에 네 오퍼레이션을 각각 별도 메서드로 구현하고 `kma_provider.py`에서 필요한 조회만 호출한다.
4. JSON/XML 원본 응답의 `response.header.resultCode`, `response.header.resultMsg`, `response.body.items.item` 구조를 검사한다. 정상 코드는 `00` 또는 문서 예제의 `0` 표현을 모두 허용하되 내부에서는 문자열 `00`으로 정규화한다.
5. `obsrValue`와 `fcstValue`를 구분하여 파싱하고, category별 단위와 결측값 규칙을 적용한다.
6. `+900` 이상 또는 `-900` 이하 값은 Missing으로 처리한다. 해상 마스킹으로 누락된 값도 Missing으로 처리하며 0으로 대체하지 않는다.
7. `PTY`·`SKY` 코드를 사람이 읽는 상태로 변환한다. 단기 `SKY`는 맑음(1)·구름많음(3)·흐림(4), `PTY`는 예보 종류별 코드표를 사용한다.
8. `RN1`·`PCP`·`SNO`의 `-`, `null`, 0은 강수·적설 없음으로 처리하되, 범주형 `PCP` 값은 원문 표시값도 보존한다.
9. `getFcstVersion` 결과로 수정 예보 여부를 확인할 정책을 정한다. 초기 버전은 조회 결과의 `version`과 조회 시각을 로그에 남긴다.
10. 기상청 호출 실패 시 임의로 Open-Meteo 결과를 섞지 말고, 비교 Tool의 부분 실패 규칙 또는 설정된 fallback 정책에 따라 명확히 처리한다.
11. 지역·기준 시각 단위의 짧은 TTL cache를 적용한다.

오류 코드는 다음 정책으로 내부 예외에 매핑한다.

- `00`: 정상
- `01`~`05`: 기상청 내부·HTTP·timeout 오류 → `KmaUpstreamError`
- `10`~`12`: 요청 파라미터·서비스 오류 → `KmaRequestError`
- `20`~`33`: 인증키·호출 제한 오류 → `KmaAuthenticationError` 또는 `KmaRateLimitError`
- `99`: 알 수 없는 오류 → `KmaUpstreamError`

MCP 응답에는 내부 exception 이름 대신 안전한 메시지, 공급자명, 재시도 가능 여부만 노출한다.

## 6. 환경 변수

```env
WEATHER_PROVIDER=kma                 # kma | open_meteo | mock
KMA_API_KEY=
KMA_BASE_URL=https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0
KMA_TIMEOUT_SECONDS=10
WEATHER_CACHE_TTL_SECONDS=300
WEATHER_MCP_HOST=127.0.0.1
WEATHER_MCP_PORT=8010
```

서비스키가 URL 인코딩된 형태인지 확인하고, 로그에 API 키와 전체 요청 URL을 출력하지 않는다.

## 7. 테스트 계획

- 도시명·좌표 검증
- 기상청 응답 category 변환 테스트
- Missing(`+900/-900`), `-`, `null`, 해상 마스킹 테스트
- KST 발표 시각 선택과 API 제공 전 호출 방지 테스트
- 단기예보 1시간·3시간 간격 및 5일 연장 응답 그룹화 테스트
- 네 가지 기상청 오퍼레이션별 요청 경로·파라미터 테스트
- `resultCode` 오류와 빈 `items` 응답 테스트
- base date/time 및 격자 좌표 계산 테스트
- 정상 응답, 빈 응답, API 오류, timeout 테스트
- mock provider를 사용한 MCP Tool 통합 테스트
- 실제 API 테스트는 별도 환경 변수와 명시적 통합 테스트로 분리

## 8. 기존 코드에서의 이전 순서

1. `services/open_meteo_client.py`로 현재 HTTP 호출을 이동한다.
2. `WeatherProvider` 인터페이스와 `WeatherService`를 추가한다.
3. 기존 `get_current_weather`, `get_weather_forecast`가 서비스를 호출하도록 변경한다.
4. `models/`의 request·response·기상청 원본 schema를 먼저 확정한다.
5. `kma_client.py`와 mapper를 추가하고 `WEATHER_PROVIDER`로 선택한다.
6. `compare_weather_sources`를 추가하고 두 Provider의 정규화 결과를 비교한다.
7. 루트 호환 진입점을 만들지 않고 `python -m mcp_server.weather`만 공식 실행 경로로 사용한다.

## 9. 구현 가능성 점검

구조와 기능 흐름은 현재 코드에 반영되어 있다. 아래는 구현 완료 여부와 남은 확장 작업을 구분한 현재 상태다.

- [x] `WeatherProvider`의 `current()`·`forecast()` Protocol과 두 Provider 구현
- [x] 기상청 endpoint와 네 가지 오퍼레이션 확정
- [x] KST 기준 KMA 실황·단기예보 발표 시각 계산
- [x] KMA category와 내부 날씨 결과의 기본 매핑
- [x] 비교 Tool의 병렬 조회, 부분 실패, 최고기온 차이 계산
- [x] Provider mock 기반 단위 테스트와 MCP discovery 통합 테스트
- [ ] `mcp`, `pydantic`, `httpx`, `python-dotenv` 버전 고정
- [ ] 실제 KMA JSON 응답 fixture 확대
- [ ] 강수량·강수확률·풍속·날씨 상태까지 비교 항목 확대
- [ ] retry·cache·typed KMA Pydantic 응답 모델 추가
- [ ] 서울·부산 외 도시 좌표 및 해외 Open-Meteo geocoding 지원

권장 구현 순서는 `models/` → Provider interface → 각 client → mapper → `WeatherService` → `tools/compare.py` → MCP 통합 테스트다.

### 완료 기준

- 기존 두 날씨 Tool의 mock·Open-Meteo 결과 필드가 리팩터링 전과 동일하다.
- `WEATHER_PROVIDER=kma`에서 실황·단기예보 조회가 동작한다.
- 비교 Tool이 두 공급자의 결과를 동일한 내부 모델로 정규화한다.
- 한 공급자 timeout 시 다른 결과와 오류 상태를 함께 반환한다.
- Tool 파일에서 `httpx`와 외부 API URL을 직접 사용하지 않는다.
