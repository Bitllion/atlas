"""Set the admin password and idempotently seed the built-in roles."""

import argparse
import sys
from pathlib import Path

from sqlalchemy import select

# Allow direct execution from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models import Role, User, UserRole


BUILTIN_ROLES = {
    "admin": "平台管理员",
    "operator": "运营人员",
    "viewer": "只读用户",
}


def set_admin_password(password: str) -> None:
    with SessionLocal.begin() as db:
        roles: dict[str, Role] = {}
        for name, description in BUILTIN_ROLES.items():
            role = db.scalar(select(Role).where(Role.name == name))
            if role is None:
                role = Role(name=name, description=description)
                db.add(role)
                db.flush()
            else:
                role.description = description
                role.deleted_at = None
            roles[name] = role

        admin = db.scalar(
            select(User).where(User.username == "admin", User.deleted_at.is_(None))
        )
        if admin is None:
            raise RuntimeError("admin 用户不存在，请先初始化 admin 用户")
        admin.password_hash = hash_password(password)
        admin.is_active = True

        binding = db.scalar(
            select(UserRole).where(UserRole.user_id == admin.id, UserRole.role_id == roles["admin"].id)
        )
        if binding is None:
            db.add(UserRole(user_id=admin.id, role_id=roles["admin"].id, granted_by=admin.id))
        else:
            binding.deleted_at = None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--password", required=True, help="admin 用户的新密码")
    args = parser.parse_args()
    set_admin_password(args.password)
    print("admin 密码与内置角色已更新。")


if __name__ == "__main__":
    main()
