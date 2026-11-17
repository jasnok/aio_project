"""Textual interface for curl."""

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static, Switch, TextArea

from turl.client import request
from turl.response import response_yaml

DEFAULT_URL = "http://localhost:5678/webhook/meeting-classify"
DEFAULT_BODY = '''{
  "title": "10월 16일 주간 회의",
  "notes": "참석: 김민지, 이준호, 박서연. 1) 신규 고객 문의 응답 템플릿을 이준호가 금요일까지 정리한다. 2) 박서연은 다음 주 월요일까지 VPN 장애 보고서를 작성한다. 3) 서버 점검 일정은 김민지가 오늘 중 공지한다. 4) 회의실 예약 규칙 개선은 담당자를 다음 회의에서 정한다. 다음 회의는 10월 23일."
}'''


class TurlApp(App):
    TITLE = "Turl — curl HTTP client"
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("enter", "send", "Send request", priority=True),
        Binding("ctrl+j", "newline", "Body newline", priority=True),
    ]
    CSS = """
    Screen { padding: 1 2; }
    #options { height: 3; align-vertical: middle; }
    #method { width: 20; }
    #options Label { width: auto; padding: 1 2; }
    #body { height: 8; }
    #send { margin: 1 0; }
    #status { height: auto; max-height: 3; }
    #responses { height: 1fr; min-height: 8; }
    #result, #yaml-result { min-height: 5; height: 1fr; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("URL")
        yield Input(value=DEFAULT_URL, placeholder="https://example.com/api", id="url")
        with Horizontal(id="options"):
            yield Select([(m, m) for m in ("GET", "POST", "PUT", "DELETE")], value="POST", allow_blank=False, id="method")
            yield Label("Send JSON")
            yield Switch(value=True, id="json")
        yield Label("Body (Ctrl+J inserts a newline)")
        yield TextArea(DEFAULT_BODY, id="body")
        yield Button("Send request", variant="primary", id="send")
        yield Static("Ready", id="status", markup=False)
        with VerticalScroll(id="responses"):
            yield Label("Response (headers and body)")
            yield TextArea(read_only=True, id="result")
            yield Label("Response as YAML (JSON body)")
            yield TextArea(read_only=True, id="yaml-result")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#url", Input).focus()
        self.busy = False

    def action_newline(self) -> None:
        body = self.query_one("#body", TextArea)
        if body.has_focus:
            body.insert("\n")

    @on(Button.Pressed, "#send")
    def button_send(self) -> None:
        self.action_send()

    def action_send(self) -> None:
        if self.busy:
            return
        self.busy = True
        self.query_one("#send", Button).disabled = True
        self.query_one("#status", Static).update("Sending request…")
        self.send_request()

    @work(exclusive=True)
    async def send_request(self) -> None:
        status = self.query_one("#status", Static)
        result = self.query_one("#result", TextArea)
        yaml_result = self.query_one("#yaml-result", TextArea)
        yaml_result.load_text("")
        try:
            response = await request(
                self.query_one("#url", Input).value,
                str(self.query_one("#method", Select).value),
                self.query_one("#body", TextArea).text,
                self.query_one("#json", Switch).value,
            )
            result.load_text(response.output + ("\n" + response.error if response.error else ""))
            yaml_result.load_text(response_yaml(response.output))
            status.update("Request complete" if response.returncode == 0 else f"curl failed (exit {response.returncode})")
        except (ValueError, OSError, TimeoutError) as exc:
            result.load_text(str(exc))
            yaml_result.load_text("YAML unavailable: request failed.")
            status.update("Request failed")
        finally:
            self.busy = False
            self.query_one("#send", Button).disabled = False


def main() -> None:
    TurlApp().run()


if __name__ == "__main__":
    main()
