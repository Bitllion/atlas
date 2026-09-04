"""Idempotently seed fine-grained permissions and built-in role mappings."""

import sys
from pathlib import Path

from sqlalchemy import or_, select

# Allow direct execution as ``python scripts/seed_permissions.py`` from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.session import SessionLocal
from app.models import Permission, Role, RolePermission, WorkflowDefinition


PURCHASE_APPROVAL_DEFINITION = {
    "nodes": [
        {"id": "n1", "type": "approval", "assignee_role": "operator", "name": "部门审批"},
        {"id": "n2", "type": "approval", "assignee_role": "admin", "name": "采购终审"},
        {"id": "end", "type": "end"},
    ],
    "edges": [
        {"source": "n1", "target": "n2"},
        {"source": "n2", "target": "end"},
    ],
}


PERMISSIONS = {
    "object.read": ("object", "read", "查看基础设施对象"),
    "object.write": ("object", "write", "创建、更新或删除基础设施对象"),
    "asset.read": ("asset", "read", "查看资产"),
    "asset.write": ("asset", "write", "管理资产入库、部署、转移、退役与恢复"),
    "purchase.read": ("purchase", "read", "查看采购申请"),
    "purchase.write": ("purchase", "write", "创建或更新采购申请"),
    "purchase.approve": ("purchase", "approve", "审批或驳回采购申请"),
    "workorder.read": ("workorder", "read", "查看工单"),
    "workorder.write": ("workorder", "write", "创建或处理工单"),
    "workflow.read": ("workorder", "read", "查看工作流定义、实例与个人待办"),
    "workflow.write": ("workorder", "write", "启动工作流并处理审批任务"),
    "knowledge.read": ("knowledge", "read", "查看知识库"),
    "knowledge.write": ("knowledge", "write", "管理知识库"),
    "import.execute": ("import", "execute", "预览、执行并查看导入任务"),
    "admin.manage": ("admin", "manage", "管理用户、组织与系统数据"),
    "dashboard.read": ("dashboard", "read", "查看运营总览"),
    "search.read": ("search", "read", "使用全局搜索"),
    "quality.read": ("quality", "read", "查看数据质量中心"),
}

ROLE_DESCRIPTIONS = {
    "admin": "平台管理员",
    "operator": "运营人员",
    "viewer": "只读用户",
}

READ_PERMISSIONS = {code for code in PERMISSIONS if code.endswith(".read")}
ROLE_PERMISSIONS = {
    "admin": set(PERMISSIONS),
    "operator": READ_PERMISSIONS
    | {
        "object.write",
        "asset.write",
        "purchase.write",
        "purchase.approve",
        "workorder.write",
        "workflow.write",
        "knowledge.write",
        "import.execute",
    },
    "viewer": READ_PERMISSIONS,
}


def seed_permissions() -> None:
    with SessionLocal.begin() as db:
        permissions: dict[str, Permission] = {}
        for code, (resource_type, action, description) in PERMISSIONS.items():
            permission = db.scalar(select(Permission).where(Permission.name == code))
            if permission is None:
                permission = Permission(name=code, resource_type=resource_type, action=action)
                db.add(permission)
            permission.resource_type = resource_type
            permission.action = action
            permission.description = description
            permission.deleted_at = None
            db.flush()
            permissions[code] = permission

        for role_name, expected_codes in ROLE_PERMISSIONS.items():
            role = db.scalar(select(Role).where(Role.name == role_name))
            if role is None:
                role = Role(name=role_name, description=ROLE_DESCRIPTIONS[role_name])
                db.add(role)
                db.flush()
            else:
                role.deleted_at = None

            for code in expected_codes:
                permission = permissions[code]
                binding = db.scalar(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == permission.id,
                    )
                )
                if binding is None:
                    db.add(RolePermission(role_id=role.id, permission_id=permission.id))
                else:
                    binding.deleted_at = None

        workflow = db.scalar(select(WorkflowDefinition).where(or_(
            WorkflowDefinition.code == "purchase_approval",
            WorkflowDefinition.name == "采购申请审批",
        )))
        if workflow is None:
            workflow = WorkflowDefinition(
                name="采购申请审批", code="purchase_approval",
                description="内置两级采购审批：部门审批后由采购终审",
                definition=PURCHASE_APPROVAL_DEFINITION,
            )
            db.add(workflow)
        else:
            workflow.name = "采购申请审批"
            workflow.code = "purchase_approval"
            workflow.description = "内置两级采购审批：部门审批后由采购终审"
            workflow.definition = PURCHASE_APPROVAL_DEFINITION
            workflow.version = 1
            workflow.is_active = True
            workflow.deleted_at = None
            workflow.deleted_by = None


def main() -> None:
    seed_permissions()
    print(f"Seeded {len(PERMISSIONS)} permissions for {len(ROLE_PERMISSIONS)} built-in roles.")


if __name__ == "__main__":
    main()
