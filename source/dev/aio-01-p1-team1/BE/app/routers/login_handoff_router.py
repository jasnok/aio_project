"""관리자 인증을 짧은 일회용 번호로 별도 화면에 전달합니다."""
import json
import secrets

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.core.api_response import ApiResponse
from app.core.admin_auth import create_admin_token, get_current_admin
from fastapi.security import HTTPAuthorizationCredentials
from app.core.redis_config import get_redis
from app.schemas.admin_schema import AdminLogin
from app.services.admin_service import admin_login_process

router = APIRouter(prefix="/login-handoff", tags=["Admin"])


class HandoffRequest(BaseModel):
    ticket: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")


@router.post("/admin")
def issue(admin: AdminLogin) -> ApiResponse:
    account = admin_login_process(admin)
    ticket = secrets.token_urlsafe(32)
    payload = json.dumps({"username": account.username, "access_token": create_admin_token(account)})
    try:
        get_redis().set("login-handoff:" + ticket, payload, ex=60)
    except Exception as error:
        raise HTTPException(503, "로그인 이동을 준비할 수 없습니다.") from error
    return ApiResponse(success=True, message="관리자 인증 완료", data={"ticket": ticket})


@router.post("/consume")
def consume(request: HandoffRequest) -> ApiResponse:
    try:
        raw = get_redis().getdel("login-handoff:" + request.ticket)
    except Exception as error:
        raise HTTPException(503, "로그인 이동을 확인할 수 없습니다.") from error
    if not raw:
        raise HTTPException(401, "이동 번호가 만료되었거나 이미 사용되었습니다. 다시 로그인해 주세요.")
    data = json.loads(raw)
    get_current_admin(HTTPAuthorizationCredentials(scheme="Bearer", credentials=data["access_token"]))
    return ApiResponse(success=True, message="관리자 로그인 완료", data=data)
