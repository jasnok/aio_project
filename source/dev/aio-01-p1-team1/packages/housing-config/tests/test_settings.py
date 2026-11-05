import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from housing_config import ConfigurationError, Settings, read_env_file, read_secrets_files


class SettingsTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / ".env"

    def write(self, text):
        self.path.write_text(text, encoding="utf-8-sig")

    def test_environment_overrides_file_and_secrets(self):
        self.write("TOKEN=file\n")
        s = Settings(self.path, lambda _: "secret", {"TOKEN": "env"})
        self.assertEqual(s.resolve("TOKEN"), ("env", "environment"))

    def test_file_overrides_secrets_without_mutating_environment(self):
        self.write("ISOLATED_TOKEN=file\n")
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(Settings(self.path, lambda _: "secret").get("ISOLATED_TOKEN"), "file")
            self.assertNotIn("ISOLATED_TOKEN", os.environ)

    def test_existing_file_does_not_hide_missing_field_in_secrets(self):
        self.write("OTHER=value\n")
        self.assertEqual(Settings(self.path, lambda _: "secret", {}).get("TOKEN"), "secret")

    def test_blank_values_fall_through(self):
        self.write("TOKEN=\n")
        self.assertEqual(Settings(self.path, lambda _: "secret", {"TOKEN": " "}).get("TOKEN"), "secret")

    def test_missing_secrets_fall_back(self):
        def missing(_):
            raise FileNotFoundError()
        self.assertEqual(Settings(self.path, missing, {}).get("TOKEN", "default"), "default")

    def test_file_edit_is_visible_without_stale_environment(self):
        self.write("TOKEN=first\n")
        s = Settings(self.path, environ={})
        self.assertEqual(s.get("TOKEN"), "first")
        self.write("TOKEN=second\n")
        self.assertEqual(s.get("TOKEN"), "second")

    def test_bom_quotes_comments_and_literal_password(self):
        self.write('export TOKEN="value # literal ${HOME}" # comment\n')
        self.assertEqual(read_env_file(self.path)["TOKEN"], "value # literal ${HOME}")

    def test_apps_do_not_share_file_values(self):
        self.write("TOKEN=one\n")
        second = self.path.with_name("second.env")
        second.write_text("TOKEN=two\n", encoding="utf-8")
        self.assertEqual(Settings(self.path, environ={}).get("TOKEN"), "one")
        self.assertEqual(Settings(second, environ={}).get("TOKEN"), "two")

    def test_required_placeholder_reports_only_name(self):
        with self.assertRaises(ConfigurationError) as context:
            Settings(self.path, environ={"TOKEN": "your-private-token"}).require("TOKEN")
        self.assertIn("TOKEN", str(context.exception))
        self.assertNotIn("your-private-token", str(context.exception))

    def test_url_normalization(self):
        s = Settings(self.path, environ={"BACKEND_URL": " https://example.com/api/ "})
        self.assertEqual(s.http_url("BACKEND_URL"), "https://example.com/api")

    def test_invalid_urls_and_embedded_secrets_are_not_echoed(self):
        for value in ("ftp://example.com", "https://u:private@example.com", "http://localhost:wrong", "https://example.com?key=private", "https://your-project.supabase.co"):
            with self.subTest(value=value), self.assertRaises(ConfigurationError) as context:
                Settings(self.path, environ={"URL": value}).http_url("URL")
            self.assertNotIn(value, str(context.exception))
            self.assertNotIn("private", str(context.exception))

    def test_project_secrets_override_global(self):
        first = self.path.with_name("global.toml")
        second = self.path.with_name("project.toml")
        first.write_text('TOKEN="global"\nOTHER="retained"', encoding="utf-8")
        second.write_text('TOKEN="project"', encoding="utf-8")
        self.assertEqual(read_secrets_files(first, second), {"TOKEN": "project", "OTHER": "retained"})

    def test_invalid_secrets_do_not_echo_contents(self):
        self.path.write_text('TOKEN=private-invalid', encoding="utf-8")
        with self.assertRaises(ConfigurationError) as context:
            read_secrets_files(self.path)
        self.assertNotIn("private-invalid", str(context.exception))
