import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core import api_client


class UserApiAuthorizationTest(unittest.TestCase):
    def test_logged_in_user_sends_supabase_token(self):
        response = SimpleNamespace(is_error=False, json=lambda: {"success": True})
        with patch.object(api_client.st, "session_state", {"access_token": "user-token"}), \
             patch.object(api_client.httpx, "request", return_value=response) as send:
            api_client.request("GET", "/profiles/user-a")
        self.assertEqual(send.call_args.kwargs["headers"],
                         {"Authorization": "Bearer user-token"})

    def test_public_request_without_login_has_no_token(self):
        response = SimpleNamespace(is_error=False, json=lambda: {"success": True})
        with patch.object(api_client.st, "session_state", {}), \
             patch.object(api_client.httpx, "request", return_value=response) as send:
            api_client.request("GET", "/listings/getall")
        self.assertIsNone(send.call_args.kwargs["headers"])
