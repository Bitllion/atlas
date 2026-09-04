"""Password hashing, JWT handling, and request authentication dependencies."""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.exceptions import ServiceError
from app.database.session import get_db
from app.models import User


password_hasher = PasswordHash((BcryptHasher(),))
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password, password_hash)
    except (TypeError, ValueError):
        # Existing placeholder values are intentionally not valid hashes.
        return False


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.auth_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def _unauthorized(message: str = "认证凭据无效或已过期") -> ServiceError:
    return ServiceError(401, "Unauthorized", message)


def _user_from_token(db: Session, token: str) -> User:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("type") != "access" or not isinstance(payload.get("sub"), str):
            raise _unauthorized()
        user_id = UUID(payload["sub"])
    except (InvalidTokenError, ValueError) as exc:
        raise _unauthorized() from exc
    user = db.scalar(
        select(User).where(User.id == user_id, User.is_active.is_(True), User.deleted_at.is_(None))
    )
    if user is None:
        raise _unauthorized()
    return user


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """Require and resolve a valid Bearer access token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("需要 Bearer 认证")
    return _user_from_token(db, credentials.credentials)


def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
    db: Session = Depends(get_db),
) -> User | None:
    """Resolve Bearer first, then the legacy dev-only user header."""
    if credentials is not None:
        if credentials.scheme.lower() != "bearer":
            raise _unauthorized()
        return _user_from_token(db, credentials.credentials)
    if authorization is not None:
        raise _unauthorized()
    if settings.auth_mode.lower() != "dev" or x_user_id is None:
        return None
    try:
        user_id = UUID(x_user_id)
    except ValueError as exc:
        raise _unauthorized("X-User-Id 格式无效") from exc
    user = db.scalar(
        select(User).where(User.id == user_id, User.is_active.is_(True), User.deleted_at.is_(None))
    )
    if user is None:
        raise _unauthorized("X-User-Id 对应用户不存在或已停用")
    return user


def require_current_user(user: User | None = Depends(get_current_user_optional)) -> User:
    # TODO(auth-rbac): add permission + resource scope + management scope checks here.
    if user is None:
        raise _unauthorized("需要认证")
    return user


def actor_id(user: User | None) -> str | None:
    return str(user.id) if user is not None else None
