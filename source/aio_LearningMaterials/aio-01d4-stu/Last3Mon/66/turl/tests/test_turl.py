from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest
from textual.widgets import Input, Select, TextArea

from turl.app import TurlApp
from turl.client import request


@pytest.fixture
def server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.reply()

        do_POST = do_GET
        do_PUT = do_GET
        do_DELETE = do_GET

        def reply(self):
            body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
            self.send_response(418 if self.path == '/error' else 200)
            self.end_headers()
            self.wfile.write(self.command.encode() + b' ' + body + b' ' + self.headers.get('Content-Type', '').encode())

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{httpd.server_port}'
    httpd.shutdown()
    httpd.server_close()
    thread.join()


@pytest.mark.parametrize('method', ['GET', 'POST', 'PUT', 'DELETE'])
async def test_real_curl(server, method):
    response = await request(server, method, '{"hello":"한글"}', True)
    assert response.returncode == 0
    assert 'HTTP/1.0 200' in response.output
    assert method in response.output
    assert '한글' in response.output
    assert 'application/json' in response.output


async def test_http_error_preserves_response(server):
    response = await request(server + '/error', 'GET', '', False)
    assert '418' in response.output


@pytest.mark.parametrize('url,body,json_mode', [('file:///etc/passwd', '', False), ('https://example.com', '{', True)])
async def test_validation(url, body, json_mode):
    with pytest.raises(ValueError):
        await request(url, 'GET', body, json_mode)


async def test_tui_enter_and_newline(server):
    app = TurlApp()
    async with app.run_test(size=(100, 40)) as pilot:
        app.query_one('#url', Input).value = server
        app.query_one('#method', Select).value = 'POST'
        body = app.query_one('#body', TextArea)
        body.load_text('{}')
        body.focus()
        await pilot.press('ctrl+j')
        assert '\n' in body.text
        await pilot.press('enter')
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert 'POST' in app.query_one('#result', TextArea).text
        assert not app.busy


async def test_tui_invalid_json(server):
    app = TurlApp()
    async with app.run_test() as pilot:
        app.query_one('#url', Input).value = server
        app.query_one('#body', TextArea).load_text('{')
        await pilot.press('enter')
        await app.workers.wait_for_complete()
        assert 'Invalid JSON' in app.query_one('#result', TextArea).text
        assert not app.busy


@pytest.mark.parametrize('body', [
    '{"title":"회의","items":[1,true,null],"nested":{"value":"yes"}}',
    '[1,2,3]', 'null', 'false', '42', '"hello"',
])
def test_yaml_preserves_json_values(body):
    import json
    import yaml
    from turl.response import response_yaml

    output = 'HTTP/1.1 200 Connection established\r\n\r\nHTTP/2 200\r\nContent-Type: application/json\r\n\r\n' + body
    assert yaml.safe_load(response_yaml(output)) == json.loads(body)


@pytest.mark.parametrize('output', ['', 'HTTP/1.1 204 No Content\r\n\r\n', '<html>Error</html>'])
def test_non_json_yaml_message(output):
    from turl.response import response_yaml
    assert response_yaml(output).startswith('YAML unavailable:')


async def test_tui_yaml_preserves_original(monkeypatch):
    import yaml
    from turl.client import Response

    original = 'HTTP/1.1 200 OK\r\n\r\n{"title":"회의","items":[1,true,null]}'

    async def fake_request(*args):
        return Response(original, '', 0)

    monkeypatch.setattr('turl.app.request', fake_request)
    app = TurlApp()
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.press('enter')
        await app.workers.wait_for_complete()
        assert app.query_one('#result', TextArea).text == original
        rendered = app.query_one('#yaml-result', TextArea).text
        assert '회의' in rendered
        assert yaml.safe_load(rendered) == {'title': '회의', 'items': [1, True, None]}
        app.query_one('#yaml-result', TextArea).scroll_visible()
        await pilot.pause()
        assert app.query_one('#yaml-result', TextArea).read_only

        async def non_json(*args):
            return Response('plain text', '', 0)

        monkeypatch.setattr('turl.app.request', non_json)
        await pilot.press('enter')
        await app.workers.wait_for_complete()
        assert app.query_one('#yaml-result', TextArea).text.startswith('YAML unavailable:')
