# 외부 API 설정

## Tour 임베딩 Provider

기본값은 프로젝트 Docker의 Ollama입니다.

```dotenv
TOUR_EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://192.100.200.232:11435
OLLAMA_EMBEDDING_MODEL=embeddinggemma
```

OpenAI 임베딩을 사용하려면 `app/tour/.env`를 다음처럼 변경합니다.

```dotenv
TOUR_EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=발급받은_API_KEY
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536
```

Provider를 바꾼 뒤 `python .\resources\database\populate_tour_documents.py`를 다시 실행해야 해당 Provider용 벡터 문서가 적재됩니다.

## OpenAI Agent

`backend/.env`의 `OPENAI_API_KEY`는 사용자의 복합 질문을 해석하고 여러 MCP Tool 결과를 하나의 답변으로 조합할 때 필요합니다. Tour가 Ollama 임베딩을 사용하더라도 Backend Agent 키는 별도로 필요합니다.

## 기상청 API

`app/weather/.env`에 다음 값을 설정합니다.

```dotenv
KMA_API_KEY=공공데이터포털_Decoding_인증키
KMA_API_BASE_URL=https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0
KMA_API_VERSION=2.0
REQUEST_TIMEOUT_SECONDS=10
```

API 버전이 바뀌면 URL과 버전을 함께 변경합니다. 자동 fallback은 응답 Schema가 달라질 위험이 있어 사용하지 않습니다. 변경 후 단위 테스트와 실제 MCP 호출을 모두 확인합니다.
