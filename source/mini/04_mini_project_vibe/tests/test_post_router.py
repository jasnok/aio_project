"""Post Router의 CRUD와 작성자 검증을 테스트합니다."""

from app.routers import post_router
from app.services.post_service import PostAuthorNotFoundError
from tests.conftest import TEST_POST_ID, TEST_USER_ID


CREATE_BODY = {"user_id": TEST_USER_ID, "title": "테스트 게시글", "content": "게시글 내용"}
UPDATE_BODY = {"title": "수정 제목", "content": "수정 내용"}


def test_create_and_list_posts(client, monkeypatch, sample_post):
    monkeypatch.setattr(post_router, "post_create", lambda post: sample_post)
    monkeypatch.setattr(post_router, "post_get_all", lambda: [sample_post])
    assert client.post("/posts", json=CREATE_BODY).status_code == 201
    assert client.get("/posts").status_code == 200


def test_get_update_delete_post(client, monkeypatch, sample_post):
    monkeypatch.setattr(post_router, "post_get", lambda post_id: sample_post)
    monkeypatch.setattr(post_router, "post_update", lambda post_id, post: sample_post)
    monkeypatch.setattr(post_router, "post_delete", lambda post_id: sample_post)
    assert client.get(f"/posts/{TEST_POST_ID}").status_code == 200
    assert client.put(f"/posts/{TEST_POST_ID}", json=UPDATE_BODY).status_code == 200
    assert client.delete(f"/posts/{TEST_POST_ID}").status_code == 200


def test_missing_post_returns_404(client, monkeypatch):
    monkeypatch.setattr(post_router, "post_get", lambda post_id: None)
    assert client.get("/posts/missing").status_code == 404


def test_missing_author_returns_404(client, monkeypatch):
    def missing_author(_post):
        raise PostAuthorNotFoundError

    monkeypatch.setattr(post_router, "post_create", missing_author)
    assert client.post("/posts", json=CREATE_BODY).status_code == 404


def test_empty_post_returns_422(client):
    assert client.post("/posts", json={"user_id": TEST_USER_ID, "title": " ", "content": " "}).status_code == 422
