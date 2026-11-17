# Tour Spot MCP

한국관광공사 TourAPI를 이용해 대한민국 국내 관광지를 검색하는 독립 MCP 서버입니다.

## 제공 Tool

- `search_tour_spots`: 국내 지역명으로 관광지를 검색합니다.

## 프로젝트 구조

- `tour_spot_server.py`: MCP 서버 조립과 실행
- `config/`: `.env` 로딩과 공통 설정 정의
- `constants/`: 지역코드와 TourAPI 고정값
- `exceptions/`: 관광지 검색 과정의 예외
- `repositories/`: TourAPI 호출과 지역코드 캐시
- `schemas/`: 지역 및 관광지 결과 데이터 형식
- `mappers/`: TourAPI 응답을 내부 Schema로 변환
- `services/`: 지역 판별과 관광지 검색 순서
- `tools/`: MCP Tool 등록

## 설정 및 실행

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

생성된 `.env`의 `TOUR_API_SERVICE_KEY`에 공공데이터포털 인증키를 입력합니다. 나머지 값은 필요할 때만 변경합니다.

```powershell
python tour_spot_server.py
```

기본 주소는 `http://127.0.0.1:8030/mcp`입니다.
