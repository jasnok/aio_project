"""Render와 로컬 환경에서 실행하는 공용 FastAPI 애플리케이션입니다."""

from fastapi import FastAPI

from app.routers.chat_router import chat_router
from app.routers.comment_router import comment_router
from app.routers.post_router import post_router
from app.routers.support_router import support_router
from app.routers.user_router import user_router


app = FastAPI(
    title="Mini Project Vibe API",
    version="1.0.0",
    description="User, Post, Comment, Support CRUD와 Gemini Chat API를 제공합니다.",
)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """외부 서비스 호출 없이 애플리케이션 실행 상태를 확인합니다."""

    return {"status": "ok"}


app.include_router(user_router)
app.include_router(post_router)
app.include_router(comment_router)
app.include_router(support_router)
app.include_router(chat_router)
