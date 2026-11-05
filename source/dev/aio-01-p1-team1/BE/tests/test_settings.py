import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.settings import get_allowed_origins, settings
from app.services.chat_service import get_summary_storage_mode


class AppSettingsTest(unittest.TestCase):
    def test_cors_and_chat_summary_use_backend_env_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("ALLOWED_ORIGINS=https://demo.example.com\nCHAT_SUMMARY_STORAGE=supabase\n", encoding="utf-8")
            with patch.object(settings, "env_path", path), patch.dict(os.environ, {}, clear=True):
                self.assertEqual(get_allowed_origins(), ["https://demo.example.com"])
                self.assertEqual(get_summary_storage_mode(), "supabase")

    def test_default_cors_does_not_allow_arbitrary_sites(self):
        with patch.object(settings, "file_values", return_value={}), patch.dict(os.environ, {}, clear=True):
            self.assertNotIn("*", get_allowed_origins())
            self.assertIn("http://127.0.0.1:8501", get_allowed_origins())
