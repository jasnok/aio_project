"""여러 테스트에서 공유하는 FastAPI Client와 샘플 모델입니다."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.comment_schema import CommentPublic
from app.schemas.post_schema import PostPublic
from app.schemas.support_schema import SupportPublic, SupportStatus
from app.schemas.user_schema import UserPublic


TEST_USER_ID = "20260723100000001"
TEST_POST_ID = "20260723101000001"
TEST_COMMENT_ID = "20260723102000001"
TEST_SUPPORT_ID = "20260723103000001"
TEST_TIME = datetime.fromisoformat("2026-07-23T10:00:00+09:00")


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def sample_user() -> UserPublic:
    return UserPublic(
        user_id=TEST_USER_ID,
        email="user@example.com",
        name="홍길동",
        created_at=TEST_TIME,
        updated_at=TEST_TIME,
    )


@pytest.fixture
def sample_post() -> PostPublic:
    return PostPublic(
        post_id=TEST_POST_ID,
        user_id=TEST_USER_ID,
        title="테스트 게시글",
        content="게시글 내용",
        created_at=TEST_TIME,
        updated_at=TEST_TIME,
    )


@pytest.fixture
def sample_comment() -> CommentPublic:
    return CommentPublic(
        comment_id=TEST_COMMENT_ID,
        post_id=TEST_POST_ID,
        user_id=TEST_USER_ID,
        content="댓글 내용",
        created_at=TEST_TIME,
        updated_at=TEST_TIME,
    )


@pytest.fixture
def sample_support() -> SupportPublic:
    return SupportPublic(
        support_id=TEST_SUPPORT_ID,
        user_id=TEST_USER_ID,
        title="문의 제목",
        content="문의 내용",
        status=SupportStatus.PENDING,
        created_at=TEST_TIME,
        updated_at=TEST_TIME,
    )
