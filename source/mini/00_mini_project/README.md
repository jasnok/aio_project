# mini_project

간단한 FastAPI 기반 백엔드 예제 프로젝트입니다.

## 개요

- `app/main.py`: FastAPI 애플리케이션 진입점
- `app/routers/chat_router.py`: Gemini 챗봇 호출 엔드포인트
- `app/routers/product_router.py`: 상품 CRUD 관련 엔드포인트
- `app/schemes`: 요청/응답 모델 정의
- `app/services`: 비즈니스 로직 처리
- `app/core/chat_config.py`: `.env` 환경 변수 로드
- `tests`: pytest 기반 테스트

## 요구 사항

- Python 3.11 이상 권장
- `requirements.txt`에 정의된 패키지

## 설치

가상환경을 사용하고 있다면 아래 명령으로 패키지를 설치합니다.

```powershell
cd C:\mini\00_mini_project
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 실행

앱을 실행하려면 Uvicorn을 사용합니다.

```powershell
cd C:\mini\00_mini_project
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

기본적으로 다음 엔드포인트를 제공합니다:

- `POST /chat/gemini`
  - 요청: `user_id`, `prompt`
  - 응답: `answer`
- `POST /product/create`
  - 요청: `id`, `name`, `price`
  - 응답: 생성된 상품 정보
- `GET /product/get/{product_id}`
  - 응답: 지정 ID 상품 정보
- `GET /product/getall`
  - 응답: 전체 상품 목록

## 환경 변수

프로젝트 루트에 `.env` 파일을 두고 다음 변수를 설정해야 합니다.

```env
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.5-flash-lite
```

`app/core/chat_config.py`에서 `.env`를 자동으로 로드합니다.

## 테스트

`pytest`로 테스트를 실행합니다.

```powershell
cd C:\mini\00_mini_project
.\.venv\Scripts\python.exe -m pytest -q
```

## 참고

- `requirements.txt`에 `pytest==8.4.2`가 포함되어 있어야 합니다.
- `py -m pytest -q` 명령이 작동하려면 활성 가상환경과 설치된 패키지가 일치해야 합니다.
