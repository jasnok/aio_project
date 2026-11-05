import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core import api_client


class AdminApiAuthorizationTest(unittest.TestCase):
    def test_admin_requests_send_token_but_login_does_not(self):
        response = SimpleNamespace(is_error=False, json=lambda: {"success": True})
        with patch.object(api_client.st, "session_state", {"admin_token": "test-token"}), \
             patch.object(api_client.httpx, "request", return_value=response) as send:
            api_client.request("GET", "/admin/favorites/ranking")
            self.assertEqual(send.call_args.kwargs["headers"],
                             {"Authorization": "Bearer test-token"})
            api_client.request("POST", "/admin/login", json={"username": "x", "password": "y"})
            self.assertIsNone(send.call_args.kwargs["headers"])

    def test_expired_token_clears_local_login_state(self):
        state = {"admin_token": "old", "admin_username": "demo", "loginout": "login"}
        response = SimpleNamespace(is_error=True, status_code=401,
                                   json=lambda: {"message": "Expired"})
        with patch.object(api_client.st, "session_state", state), \
             patch.object(api_client.httpx, "request", return_value=response):
            with self.assertRaises(api_client.BackendAPIError):
                api_client.request("GET", "/logs")
        self.assertEqual(state["loginout"], "logout")
        self.assertEqual(state["admin_token"], "")
