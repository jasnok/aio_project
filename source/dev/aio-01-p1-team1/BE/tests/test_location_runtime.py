import unittest
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from app.core.location_runtime import get_location_client, parallel_categories, close_location_runtime


class LocationRuntimeTests(unittest.TestCase):
    def tearDown(self):
        close_location_runtime()

    def test_categories_start_together_but_output_keeps_category_order(self):
        barrier = threading.Barrier(3)
        def load(category):
            barrier.wait(timeout=2)
            return category
        self.assertEqual(parallel_categories(load), ['subway', 'mart', 'hospital'])

    def test_one_failure_propagates_and_future_request_can_recover(self):
        def load(category):
            if category == 'mart':
                raise ValueError('provider failed')
            return category
        with self.assertRaises(ValueError):
            parallel_categories(load)
        self.assertEqual(parallel_categories(lambda category: category), ['subway', 'mart', 'hospital'])

    def test_four_requests_reuse_one_tcp_connection(self):
        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'
            def do_GET(self):
                self.send_response(200); self.send_header('Content-Length', '2'); self.end_headers()
                self.wfile.write(b'{}')
            def log_message(self, *args):
                pass
        class Server(ThreadingHTTPServer):
            connections = 0
            daemon_threads = True
            def get_request(self):
                self.connections += 1
                return super().get_request()
        server = Server(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            for _ in range(4):
                self.assertEqual(get_location_client().get(f'http://127.0.0.1:{server.server_port}').status_code, 200)
            self.assertEqual(server.connections, 1)
        finally:
            close_location_runtime(); server.shutdown(); server.server_close(); thread.join(timeout=2)
