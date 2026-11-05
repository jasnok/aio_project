"""Support Router의 CRUD와 상태값 검증을 테스트합니다."""

from app.routers import support_router
from app.services.support_service import SupportAuthorNotFoundError
from tests.conftest import TEST_SUPPORT_ID, TEST_USER_ID


CREATE_BODY = {
    "user_id": TEST_USER_ID,
    "title": "문의 제목",
    "content": "문의 내용",
    "status": "pending",
}
UPDATE_BODY = {"title": "수정 문의", "content": "수정 내용", "status": "answered"}


def test_create_and_list_supports(client, monkeypatch, sample_support):
    monkeypatch.setattr(support_router, "support_create", lambda support: sample_support)
    monkeypatch.setattr(support_router, "support_get_all", lambda: [sample_support])
    assert client.post("/supports", json=CREATE_BODY).status_code == 201
    assert client.get("/supports").status_code == 200


def test_get_update_delete_support(client, monkeypatch, sample_support):
    monkeypatch.setattr(support_router, "support_get", lambda support_id: sample_support)
    monkeypatch.setattr(support_router, "support_update", lambda support_id, support: sample_support)
    monkeypatch.setattr(support_router, "support_delete", lambda support_id: sample_support)
    assert client.get(f"/supports/{TEST_SUPPORT_ID}").status_code == 200
    assert client.put(f"/supports/{TEST_SUPPORT_ID}", json=UPDATE_BODY).status_code == 200
    assert client.delete(f"/supports/{TEST_SUPPORT_ID}").status_code == 200


def test_missing_support_returns_404(client, monkeypatch):
    monkeypatch.setattr(support_router, "support_get", lambda support_id: None)
    assert client.get("/supports/missing").status_code == 404


def test_missing_support_author_returns_404(client, monkeypatch):
    def missing_author(_support):
        raise SupportAuthorNotFoundError

    monkeypatch.setattr(support_router, "support_create", missing_author)
    assert client.post("/supports", json=CREATE_BODY).status_code == 404


def test_invalid_support_status_returns_422(client):
    body = {**CREATE_BODY, "status": "invalid"}
    assert client.post("/supports", json=body).status_code == 422
