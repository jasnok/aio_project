# TURL

Textual 기반 터미널 HTTP 클라이언트입니다. 별도 curl 프로세스로 요청을 실행하고 응답 헤더와 본문을 표시합니다.

## 실행

Python 3.11 이상, uv, curl이 필요합니다.

```bash
uv sync
uv run turl
```

## 사용

1. URL을 입력합니다. HTTP와 HTTPS를 지원합니다.
2. GET, POST, PUT, DELETE 중 메서드를 선택합니다.
3. JSON을 보낼 때 Send JSON을 켜고 Body에 유효한 JSON을 입력합니다.
4. Enter 또는 Send request 버튼으로 실행합니다.
5. Response에서 HTTP 상태, 헤더, 본문을 확인합니다.

Body의 줄바꿈은 Ctrl+J, 종료는 Ctrl+Q입니다. 실행 중 중복 전송은 막습니다. JSON 토글을 끄면 본문을 그대로 보내며 curl의 기본 Content-Type이 적용됩니다. 본문은 UTF-8로 전송합니다.

연결 제한은 10초, 전체 요청 제한은 60초입니다. HTTP 4xx·5xx도 응답으로 표시하므로 응답의 상태 코드를 확인하세요. 네트워크 오류는 curl 종료 코드와 메시지로 표시합니다. 응답은 텍스트로 표시하며 바이너리 응답은 지원하지 않습니다.

## 검증

```bash
uv run pytest -q
```

로컬 HTTP 서버에 실제 curl 요청을 전송하여 메서드·본문·JSON 헤더·HTTP 오류 응답을 확인하고, TUI에서 Enter 실행과 줄바꿈·입력 오류를 검사합니다.

## 로컬 Git 백업

로컬 백업 저장소는 프로젝트 내부 `.local-git/turl.git`이다. 외부 서버로 전송하지 않고 다음 명령으로 저장한다.

```bash
git push /mnt/c/aio-01d4-stu/Last3Mon/66/turl/.local-git/turl.git main
```

상위 저장소의 main 이력을 백업한다. 같은 디스크 안의 복사본이므로 디스크 고장에 대비한 백업은 아니다.

## YAML 응답 보기

기존 Response 영역의 원본 헤더와 본문은 그대로 유지된다. 아래의 **Response as YAML (JSON body)** 영역에서 JSON 본문을 YAML로 변환한 내용을 볼 수 있다. 한글과 중첩 객체, 배열을 지원하며 변환 결과는 읽기 전용이다. 화면이 작으면 응답 영역을 스크롤하여 확인한다.

JSON이 아닌 본문이나 빈 응답에는 변환 불가 안내가 표시된다. 요청 실패 시에는 YAML 영역에도 실패 안내를 표시한다.

## 기본 요청

실행 시 URL은 `http://localhost:5678/webhook/meeting-classify`, 메서드는 POST, JSON 전송은 켜짐으로 설정된다. Body에는 10월 16일 주간 회의의 제목과 회의 메모가 미리 입력된다. 필요에 따라 수정하고 Enter로 전송한다. 실행만으로 요청을 자동 전송하지는 않는다.
