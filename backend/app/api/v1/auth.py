"""Authentication endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceError
from app.core.security import create_access_token, hash_password, require_current_user, verify_password
from app.database.session import get_db
from app.models import Role, User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1024)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=1024)
    new_password: str = Field(min_length=8, max_length=1024)


def _roles(db: Session, user_id) -> list[str]:
    return list(
        db.scalars(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user_id,
                UserRole.deleted_at.is_(None),
                Role.deleted_at.is_(None),
            )
            .order_by(Role.name)
        )
    )


def user_out(db: Session, user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "organization_id": user.organization_id,
        "roles": _roles(db, user.id),
    }


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(
        select(User).where(
            User.username == payload.username,
            User.is_active.is_(True),
            User.deleted_at.is_(None),
        )
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise ServiceError(401, "InvalidCredentials", "用户名或密码错误")
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return {
        "access_token": create_access_token(str(user.id)),
        "token_type": "bearer",
        "user": user_out(db, user),
    }


@router.get("/me")
def me(user: User = Depends(require_current_user), db: Session = Depends(get_db)):
    return user_out(db, user)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise ServiceError(401, "InvalidCredentials", "当前密码错误")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "密码修改成功"}
