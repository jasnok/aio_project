# 시스템 구성 및 기능 흐름

## 1. 폴더별 책임

```text
aio-01-p1-team1/
├─ BE/          FastAPI API, Pydantic 검증, Supabase DB·Storage 연동
├─ FE_Admin/    관리자 로그인, 청약정보 등록·수정·조회·삭제
├─ FE_User/     사용자 인증, 청약정보 조회·검색·정렬
└─ docs/        설계서와 발표 자료
```

| 계층 | 주요 파일 | 책임 |
| --- | --- | --- |
| 사용자 UI | `FE_User/app_pages/03_listings.py` | 공고 검색·정렬·페이지 이동·상세 표시 |
| 관리자 UI | `FE_Admin/app_pages/02_listing_create.py` | 수동 등록 폼, 입력 유지·초기화, 이미지 선택 |
| 관리자 UI | `FE_Admin/app_pages/03_listing_manage.py` | 조회·수정·이미지 관리·선택 삭제 |
| API Client | 각 프런트의 `clients/listing_client.py` | FastAPI 요청과 오류 전달 |
| API Router | `BE/app/routers/listing_router.py` | 공개 조회·검색 API |
| API Router | `BE/app/routers/admin_router.py` | 관리자 등록·수정·삭제·이미지 API |
| Service | `BE/app/services/listing_service.py` | DB 조회·정렬·페이지·이미지 관계 처리 |
| Service | `BE/app/services/image_service.py` | 이미지 검증·Storage 업로드·정리 |
| Schema | `BE/app/schemas/listing_schema.py` | 요청·응답 타입 및 필수값 검증 |

## 2. 관리자 기능

### 청약정보 등록

- 공고명, 주택명, 면적, 모집인원, 지역·상세주소, 보증금, 월세, 신청기간, 설명, 원문 URL 입력
- JPEG·PNG·WebP 이미지 최대 20장 등록
- 이미지 한 장 최대 5MB, 전체 요청 최대 60MB
- 첫 번째 이미지를 대표 이미지로 사용
- 등록 성공 후 입력값 유지: 비슷한 주택형을 연속 등록할 때 반복 입력 감소
- `입력 초기화` 버튼으로 새 공고 입력 시 한 번에 비움
- 금액에 쉼표와 억·만 단위 읽기 표시

### 청약정보 조회·수정·삭제

- 한 페이지에 10건씩 조회
- 검색 조건과 페이지 상태 유지
- 브라우저 뒤로가기로 이전 목록·수정 화면 복원
- 기존 이미지 유지, 개별 삭제, 추가 등록, 순서 보존
- 현재 페이지 전체 선택·선택 해제·선택 삭제
- 삭제 전 대상 이름과 건수를 다시 확인
- 성공·실패 건수를 구분해 표시

## 3. 사용자 기능

### 청약정보 조회

- 지역, 최대 보증금, 최대 월세 검색
- 신청 마감이 가까운 공고를 기본 우선 표시
- 마감 공고는 흐리게 표시하고 목록 뒤로 이동
- `D-3`, `D-DAY`, `마감` 형태로 기한 표시
- 한 페이지에 10건씩 표시하고 URL에 페이지 번호 유지
- 전용면적을 `㎡`와 약식 `평`으로 함께 표시
- 금액을 쉼표 및 억·만 단위로 표시
- 여러 이미지를 갤러리로 확인
- 원문 링크를 통해 최종 공고 확인

### 정렬 기준

현재 구현에는 총 10가지 정렬 기준이 있습니다.

1. 등록 최신순
2. 신청 종료일 빠른순
3. 면적 넓은 순
4. 면적 좁은 순
5. 모집인원 많은 순
6. 모집인원 적은 순
7. 보증금 높은 순
8. 보증금 낮은 순
9. 월세 높은 순
10. 월세 낮은 순

정렬은 프런트엔드가 받은 10건만 재정렬하지 않고 백엔드와 DB가 전체 데이터에 적용합니다.

## 4. 주요 API

| Method | URL | 설명 |
| --- | --- | --- |
| GET | `/listings/getall` | 전체 공고 조회 |
| GET | `/listings/page` | 페이지 단위 조회 |
| GET | `/listings/search` | 지역·보증금·월세 조건 검색 |
| GET | `/listings/get/{listing_id}` | 공고 상세 조회 |
| POST | `/admin/listings/create` | 공고 등록 |
| POST | `/admin/listings/images/bulk` | 이미지 여러 장 업로드 |
| PUT | `/admin/listings/update/{listing_id}` | 공고 정보 수정 |
| PUT | `/admin/listings/{listing_id}/images` | 공고 이미지 목록 교체 |
| DELETE | `/admin/listings/delete/{listing_id}` | 공고 및 연결 이미지 삭제 |

## 5. 오류·빈 데이터 처리

| 상황 | 처리 |
| --- | --- |
| 검색 결과 없음 | 빈 결과 안내 표시 |
| 잘못된 정렬 값 | FastAPI 400 응답과 가능한 기준 안내 |
| 없는 공고 ID | 404 응답 |
| 이미지 형식·크기 오류 | 업로드 전후 검증 후 이유 표시 |
| 다중 이미지 업로드 일부 실패 | 이미 업로드된 파일 정리 후 전체 실패 처리 |
| 마지막 페이지의 공고 삭제 | 유효한 마지막 페이지로 자동 보정 |
| 선택 삭제 일부 실패 | 성공 건수와 실패 건수를 나눠 표시 |
