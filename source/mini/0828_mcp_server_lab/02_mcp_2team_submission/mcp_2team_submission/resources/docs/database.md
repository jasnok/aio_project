# Tour DB 준비

PostgreSQL과 pgvector를 준비한 후 `resources/database/sql/`의 SQL을 번호 순서대로 적용합니다.

1. `001_hotels.sql`: 호텔 테이블과 데이터
2. `002_attractions.sql`: 관광지 테이블과 데이터
3. `003_tour_documents.sql`: RAG 검색 문서와 vector 컬럼
4. `004_hotel_policies.sql`: 검증용 가상 호텔 정책 600건

개발용 관광지 원본 샘플은 `resources/data/tourist_attractions.mock.json`에 있습니다.

DB를 준비한 다음 루트에서 다음 명령으로 임베딩 문서를 적재합니다.

```powershell
python .\resources\database\populate_tour_documents.py
```

기본 Ollama 구성에는 `DATABASE_URL`, `TOUR_EMBEDDING_PROVIDER=ollama`, `OLLAMA_BASE_URL`, `OLLAMA_EMBEDDING_MODEL`이 필요합니다. OpenAI를 선택하면 `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`, `OPENAI_EMBEDDING_DIMENSIONS`도 설정합니다.

기존 DB를 갱신할 때는 다음 명령을 사용합니다.

```powershell
.\run\migrate_database.ps1
```

정책 데이터는 프로젝트 동작 검증을 위해 만든 임의 데이터이며 실제 예약 약관으로 사용하면 안 됩니다.
