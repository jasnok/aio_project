"""Comment Router의 CRUD와 게시글 검증을 테스트합니다."""

from app.routers import comment_router
from app.services.comment_service import CommentPostNotFoundError
from tests.conftest import TEST_COMMENT_ID, TEST_POST_ID, TEST_USER_ID


CREATE_BODY = {"user_id": TEST_USER_ID, "content": "댓글 내용"}
UPDATE_BODY = {"content": "수정 댓글"}


def test_create_and_list_comments(client, monkeypatch, sample_comment):
    monkeypatch.setattr(comment_router, "comment_create", lambda post_id, comment: sample_comment)
    monkeypatch.setattr(comment_router, "comment_get_all", lambda: [sample_comment])
    assert client.post(f"/posts/{TEST_POST_ID}/comments", json=CREATE_BODY).status_code == 201
    assert client.get("/comments").status_code == 200


def test_get_comments_by_post(client, monkeypatch, sample_comment):
    monkeypatch.setattr(comment_router, "comment_get_by_post", lambda post_id: [sample_comment])
    response = client.get(f"/posts/{TEST_POST_ID}/comments")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


def test_get_update_delete_comment(client, monkeypatch, sample_comment):
    monkeypatch.setattr(comment_router, "comment_get", lambda comment_id: sample_comment)
    monkeypatch.setattr(comment_router, "comment_update", lambda comment_id, comment: sample_comment)
    monkeypatch.setattr(comment_router, "comment_delete", lambda comment_id: sample_comment)
    assert client.get(f"/comments/{TEST_COMMENT_ID}").status_code == 200
    assert client.put(f"/comments/{TEST_COMMENT_ID}", json=UPDATE_BODY).status_code == 200
    assert client.delete(f"/comments/{TEST_COMMENT_ID}").status_code == 200


def test_missing_post_for_comment_returns_404(client, monkeypatch):
    def missing_post(_post_id, _comment):
        raise CommentPostNotFoundError

    monkeypatch.setattr(comment_router, "comment_create", missing_post)
    assert client.post("/posts/missing/comments", json=CREATE_BODY).status_code == 404


def test_empty_comment_returns_422(client):
    assert client.post(f"/posts/{TEST_POST_ID}/comments", json={"user_id": TEST_USER_ID, "content": " "}).status_code == 422
