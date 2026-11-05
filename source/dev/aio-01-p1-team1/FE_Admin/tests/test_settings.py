import os
import unittest
from unittest.mock import patch

from core.api_client import _get_backend_url
from core.settings import settings


class BackendSettingsTest(unittest.TestCase):
    def test_backend_url_uses_env_file(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(settings, "file_values", return_value={"BACKEND_URL": "https://demo.example.com/"}):
            self.assertEqual(_get_backend_url(), "https://demo.example.com")

    def test_unrelated_env_field_does_not_hide_secrets(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(settings, "file_values", return_value={"GEMINI_MODEL": "example"}), patch.object(settings, "secret_getter", return_value="https://demo.example.com"):
            self.assertEqual(_get_backend_url(), "https://demo.example.com")
