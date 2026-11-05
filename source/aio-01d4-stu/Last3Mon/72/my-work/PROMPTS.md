# Lab 02 작업 요청과 구현 기록

2026-10-26 사용자가 직접 구현·push·test·bench까지 요청함.

1. 예제 1: 데이터 조회 후 T-?\\d{4} 접수 번호 우선, FAQ 결과가 있으면 faq, 모르면 분류 LLM. 동일 category 계약으로 합류. steps와 llm_calls는 실제 실행 기준.
2. 예제 2: 정규화한 질문 키, ttl 600초, FAQ만 저장. ticket과 no_cache는 읽기·쓰기 모두 생략. 캐시 404는 미적중. HTTP 저장 응답 대신 원래 결과 반환.
3. 예제 3: 캐시 초기화 후 동일 VPN 5회와 no_cache 5회 비교. 각 bench 출력 및 stats를 runs/lab02-*.txt,json으로 보관.
4. 과제 1: Review와 모델을 Code 검사로 교체. 빈 답·한글·400자 검사. 합니다체·3문장과 사실 유지 지시는 Answer에 둠. 규칙 경로 LLM 1회, 미분류 경로 2회.
5. 과제 2: 질문 캐시 미적중 뒤 데이터 조회·규칙 분류 후 FAQ 번호 캐시. faq-<id>, ttl 600. 두 키 저장, cache_by question/faq/null. 접수·no_cache 제외.

## 구현 방식
검증된 reference 예제의 노드 구성을 바탕으로 my-work/build_lab02.py에서 단계별 워크플로우를 생성한다. reference와 기존 테스트는 수정하지 않는다. 생성기는 my-work/helpdesk.json만 갱신한다. 1=규칙, 2=질문 캐시, 3=Code 검토, 4=FAQ 캐시.

## 기록
- 기준 lab01 4/4, VPN LLM 3회, p50 3.08s / p95 3.45s.
- 예제1 lab02 앞 네 케이스 통과. 전체 8/9이며 질문 캐시 케이스만 예상 실패. VPN LLM 2회, p50 2.50s / p95 2.60s.
- 캐시 노드 복제 시 ID 중복으로 최초 import 실패. 생성 단계에서 노드 이름별 고유 UUID를 부여해 해결. check만으로 서버 import의 모든 제약을 검증하지 못함.
