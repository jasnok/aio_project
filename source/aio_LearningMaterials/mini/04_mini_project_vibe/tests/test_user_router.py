"""User Router의 성공, 검증, 예외 응답을 테스트합니다."""

from app.routers import user_router
from app.services.user_service import DuplicateEmailError
from tests.conftest import TEST_USER_ID


USER_BODY = {"email": "user@example.com", "password": "safe-password", "name": "홍길동"}


def test_create_user(client, monkeypatch, sample_user):
    monkeypatch.setattr(user_router, "user_create", lambda user: sample_user)
    response = client.post("/users", json=USER_BODY)
    assert response.status_code == 201
    assert response.json()["data"]["user_id"] == TEST_USER_ID
    assert "password" not in response.json()["data"]


def test_get_users(client, monkeypatch, sample_user):
    monkeypatch.setattr(user_router, "user_get_all", lambda: [sample_user])
    response = client.get("/users")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


def test_get_update_delete_user(client, monkeypatch, sample_user):
    monkeypatch.setattr(user_router, "user_get", lambda user_id: sample_user)
    monkeypatch.setattr(user_router, "user_update", lambda user_id, user: sample_user)
    monkeypatch.setattr(user_router, "user_delete", lambda user_id: sample_user)
    assert client.get(f"/users/{TEST_USER_ID}").status_code == 200
    assert client.put(f"/users/{TEST_USER_ID}", json=USER_BODY).status_code == 200
    assert client.delete(f"/users/{TEST_USER_ID}").status_code == 200


def test_missing_user_returns_404(client, monkeypatch):
    monkeypatch.setattr(user_router, "user_get", lambda user_id: None)
    assert client.get("/users/missing").status_code == 404


def test_duplicate_email_returns_409(client, monkeypatch):
    def duplicate(_user):
        raise DuplicateEmailError

    monkeypatch.setattr(user_router, "user_create", duplicate)
    assert client.post("/users", json=USER_BODY).status_code == 409


def test_invalid_user_input_returns_422(client):
    response = client.post("/users", json={"email": "invalid", "password": "short", "name": " "})
    assert response.status_code == 422
