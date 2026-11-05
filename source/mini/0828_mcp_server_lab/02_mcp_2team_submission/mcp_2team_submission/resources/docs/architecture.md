# 아키텍처

두 MCP 서버는 서로 독립적으로 실행되며 공통 계층을 억지로 공유하지 않습니다.

## Tour MCP

```text
server → tools → services → repositories → database
                    └──────→ rag
```

- `tools`: MCP 입력을 Schema로 검증하고 서비스를 호출합니다.
- `services`: 구조 검색, 벡터 검색, fallback 및 추천 정책을 결정합니다.
- `repositories`: PostgreSQL과 pgvector SQL을 관리합니다.
- `database`: 연결 생성과 공통 조회를 담당하며, 향후 트랜잭션·상태 점검 모듈을 추가할 수 있습니다.
- `rag`: 검색 문서 생성, OpenAI/Ollama Provider 선택, 벡터 변환을 담당합니다.

호텔 정책 검색은 반드시 먼저 검색된 호텔의 `hotel_id` 목록 안에서만 수행합니다. 임베딩 Provider가 일시적으로 실패하면 정책 테이블의 구조 검색으로 fallback하지만, 정상 상태에서는 선택한 Provider·모델·차원과 일치하는 벡터 문서만 검색합니다.

## Weather MCP

```text
server → tools → services → external_clients
```

- `services`: 발표 시각 계산과 기상 데이터 변환 규칙을 담당합니다.
- `external_clients`: 기상청 HTTP 요청과 응답 오류 처리를 담당합니다.

`config.py`와 `errors.py`는 각 서버의 `core/`에 모읍니다. 서버 폴더의 최상위에는 실행 진입점인 `main.py`만 두어 구조를 빠르게 파악할 수 있게 했습니다.
