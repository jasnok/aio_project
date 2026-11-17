# Lab 01 · 입력 검증과 규칙 차단 요청문

```plaintext
my-work/secure-agent.json 은 reference/open-it-agent.json 을 복사한 것이야. 웹훅 경로를 my-secure, 이름을 "73 Secure IT agent (my)"로.
IT help agent 앞에 관문을 넣어 줘 (AGENTS.md 3절, 5절).

1. Check employee:
   GET http://data-api:8800/employees/<encodeURIComponent(body.user)>.
   Never Error를 켜 줘 (neverError: true).
   options 구조는 {"response":{"response":{"neverError":true}}}.

2. Validate input(Code):
   question을 trim.
   비었으면 question_required,
   500자 넘으면 too_long,
   Check employee 결과에 error가 있거나 name이 없으면 unknown_user.
   해당하는 코드를 codes 배열에 모두 담아 줘.

3. Valid? false →
   Reject invalid(Respond HTTP 400, {error:'invalid request', codes}).
   잘못된 입력은 LLM을 호출하지 않아야 해.

4. Injection rules(Code):
   아래 정규식 중 하나라도 맞으면 blocked. 모두 i 플래그.
   (이전|앞의|위의|지금까지의?)\s*(지시|지침|명령)\S*\s*(모두|다)?\s*(무시|잊)
   ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|rules)
   (시스템|system)\s*(프롬프트|prompt)
   (개발자|디버그|developer|debug)\s*(모드|mode)

5. Blocked by rule? true →
   Blocked(Set:
     route "차단",
     answer "보안 정책상 처리할 수 없는 요청입니다. 필요한 내용은 IT 문의 창구로 연락해 주세요.",
     tools_used [],
     reason=맞은 규칙
   ) → Send blocked.
   false → IT help agent.

기대 결과 cases/lab01.json.
```
