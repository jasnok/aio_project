"""Short-lived, signed credentials for the existing local admin accounts."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from housing_config import is_placeholder

from app.core.settings import get_setting
from app.core.supabase_config import get_supabase
from app.schemas.admin_schema import AdminPublic


TOKEN_LIFETIME = timedelta(hours=1)
ISSUER = "housing-admin-api"
AUDIENCE = "housing-admin"
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedAdmin:
    id: int
    username: str


def _secret() -> str:
    secret = get_setting("ADMIN_TOKEN_SECRET")
    if is_placeholder(secret) or len(secret.encode("utf-8")) < 32:
        raise RuntimeError("ADMIN_TOKEN_SECRET must contain at least 32 UTF-8 bytes.")
    return secret


def create_admin_token(admin: AdminPublic) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(admin.id), "username": admin.username, "iss": ISSUER,
         "aud": AUDIENCE, "iat": now, "exp": now + TOKEN_LIFETIME},
        _secret(), algorithm="HS256",
    )


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedAdmin:
    denied = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                           detail="관리자 로그인이 필요합니다.")
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise denied
    try:
        claims = jwt.decode(credentials.credentials, _secret(), algorithms=["HS256"],
                            issuer=ISSUER, audience=AUDIENCE,
                            options={"require": ["sub", "username", "iat", "exp", "iss", "aud"]})
        admin_id = int(claims["sub"])
        if admin_id <= 0:
            raise ValueError("Invalid admin ID")
    except (jwt.PyJWTError, ValueError, TypeError) as error:
        raise denied from error

    # Deleted or renamed admins lose access even before the token expires.
    try:
        rows = (get_supabase().table("admins").select("id,username")
                .eq("id", admin_id).limit(1).execute().data)
    except Exception as error:
        raise HTTPException(status_code=503, detail="관리자 인증을 확인할 수 없습니다.") from error
    if not rows or rows[0]["username"] != claims["username"]:
        raise denied
    return AuthenticatedAdmin(id=admin_id, username=claims["username"])
