"""Authorization boundaries must hold at HTTP routes, not just in Streamlit."""

import os
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import jwt
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.admin_auth import AUDIENCE, ISSUER, create_admin_token, get_current_admin
from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.routers.admin_router import admin_login_router, admin_router
from app.routers.favorite_router import favorite_router
from app.routers.log_router import log_router
from app.routers.profile_router import profile_router
from app.schemas.admin_schema import AdminPublic


SECRET = "test-only-admin-signing-secret-of-at-least-32-bytes"
ADMIN = AdminPublic(id=7, username="demo-admin", created_at=datetime.now(timezone.utc))


class ApiAuthorizationTest(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"ADMIN_TOKEN_SECRET": SECRET})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.app = FastAPI()
        for router in (admin_login_router, admin_router, log_router, favorite_router, profile_router):
            self.app.include_router(router)
        self.client = TestClient(self.app)

    def test_admin_login_is_public_but_protected_routes_are_not(self):
        with patch("app.routers.admin_router.admin_login_process", return_value=ADMIN):
            login = self.client.post("/admin/login", json={"username": "demo-admin", "password": "valid"})
        self.assertEqual(login.status_code, 200)
        self.assertIn("access_token", login.json()["data"])
        for path in ("/admin/favorites/ranking", "/logs", "/logs/history"):
            self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.post("/admin/listings/create", json={}).status_code, 401)

    def test_example_secret_cannot_sign_tokens(self):
        with patch.dict(os.environ, {"ADMIN_TOKEN_SECRET": "your-random-admin-token-secret-at-least-32-bytes"}):
            with self.assertRaises(RuntimeError):
                create_admin_token(ADMIN)

    def test_valid_token_requires_a_still_existing_admin(self):
        token = create_admin_token(ADMIN)
        db = MagicMock()
        db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
            SimpleNamespace(data=[{"id": 7, "username": "demo-admin"}]))
        with patch("app.core.admin_auth.get_supabase", return_value=db), \
             patch("app.routers.admin_router.favorite_ranking", return_value=[]):
            response = self.client.get("/admin/favorites/ranking",
                                       headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)
        db.table.assert_called_with("admins")

    def test_tampered_expired_and_deleted_admin_tokens_are_denied(self):
        valid = create_admin_token(ADMIN)
        now = datetime.now(timezone.utc)
        expired = jwt.encode({"sub": "7", "username": "demo-admin", "iss": ISSUER,
                              "aud": AUDIENCE, "iat": now - timedelta(hours=2),
                              "exp": now - timedelta(hours=1)}, SECRET, algorithm="HS256")
        fake_db = MagicMock()
        fake_db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
            SimpleNamespace(data=[]))
        with patch("app.core.admin_auth.get_supabase", return_value=fake_db):
            for token in (valid + "x", expired, valid):
                response = self.client.get("/admin/favorites/ranking",
                                           headers={"Authorization": f"Bearer {token}"})
                self.assertEqual(response.status_code, 401)

    def test_user_routes_require_a_login(self):
        self.assertEqual(self.client.get("/profiles/user-a").status_code, 401)
        self.assertEqual(self.client.get("/favorites/mypage/user-a").status_code, 401)
        self.assertEqual(self.client.post("/favorites/create", json={"user_id": "user-a", "listing_id": 1}).status_code, 401)

    def test_user_cannot_access_another_users_profile_or_favorites(self):
        self.app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
            id="user-a", email="a@example.test")
        calls = [
            ("get", "/profiles/user-b", None),
            ("put", "/profiles/user-b", {"nickname": "x", "phone": "010-0000-0000", "interests": []}),
            ("get", "/favorites/mypage/user-b", None),
            ("post", "/favorites/create", {"user_id": "user-b", "listing_id": 1}),
            ("delete", "/favorites/delete/user-b/1", None),
        ]
        for method, path, data in calls:
            response = self.client.request(method, path, json=data)
            self.assertEqual(response.status_code, 403, (method, path, response.text))

    def test_own_profile_can_still_be_read(self):
        self.app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
            id="user-a", email="a@example.test")
        with patch("app.routers.profile_router.profile_get", return_value={"id": "user-a"}):
            response = self.client.get("/profiles/user-a")
        self.assertEqual(response.status_code, 200)
