import unittest
from types import SimpleNamespace
from housing_common.http_response import decode_response


class HttpResponseTests(unittest.TestCase):
    def test_json_array_is_safe_error(self):
        response = SimpleNamespace(json=lambda: [], is_error=False)
        with self.assertRaisesRegex(RuntimeError, 'JSON 객체'):
            decode_response(response, RuntimeError)

    def test_bad_error_details_do_not_mask_server_message(self):
        response = SimpleNamespace(json=lambda: {'message': '잠시 후 다시 시도', 'errors': ['bad', {'field': 'title', 'message': '필수'}]}, is_error=True, status_code=503)
        with self.assertRaisesRegex(RuntimeError, '잠시 후 다시 시도 title: 필수.*503'):
            decode_response(response, RuntimeError)
