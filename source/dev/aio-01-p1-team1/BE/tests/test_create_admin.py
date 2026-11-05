import contextlib
import io
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from scripts import create_admin


class CreateAdminTest(unittest.TestCase):
    def test_created_account_does_not_print_password_hash(self):
        client = MagicMock()
        client.table.return_value.insert.return_value.execute.return_value = SimpleNamespace(data=[{"username": "demo", "password": "private-hash"}])
        output = io.StringIO()
        with patch.object(create_admin, "get_supabase", return_value=client), patch.object(create_admin, "hash_password", return_value="private-hash"), contextlib.redirect_stdout(output):
            create_admin.create_admin("demo", "private-password")
        self.assertIn("demo", output.getvalue())
        self.assertNotIn("private-hash", output.getvalue())
        self.assertNotIn("private-password", output.getvalue())
