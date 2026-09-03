# Atlas 权限与多组织模型设计

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | 平台能力设计文档 |

## 1. 目标

支持企业内部、客户环境、供应商、多数据中心、多项目和多组织场景，确保用户只能访问和操作授权范围内的资源。

## 2. 组织、用户和角色

```text
Organization → User → Role → Permission
```

组织可以是 Atlas 企业、客户或供应商。资源分别表达 Owner、Operator、Maintainer 和 Viewer。

角色示例：Asset Manager、Operation Engineer、Customer Viewer、Vendor Engineer。

## 3. 权限与资源范围

```text
User → Role → Permission → Resource Scope → Management Scope
```

操作可包括 VIEW、EDIT、DELETE、MAINTAIN 和 TRANSFER。用户可能只能访问 Customer A 的 GB300，不能访问 Customer B。

## 4. 管理范围

资产属于 Atlas 公司但部署在客户环境时，可能只有 Hardware Maintenance Only 权限：可查看资产、创建维修记录和更新硬件状态，但不能登录系统、修改 OS 或执行命令。

供应商只能访问指定设备和故障信息，不能查看商业资产信息或其他客户资源。

## 5. 组织-资源授权模型

### 5.1 三类组织角色与对象字段对应

`objects` 表的多组织字段与组织角色的对应关系：

| 组织角色 | 对应字段 | 权限范围 | 典型场景 |
| --- | --- | --- | --- |
| **Owner** | `owner_org_id` | 完全控制（查看/修改/转移/退役） | Atlas 公司拥有的自有资产 |
| **Operator** | `operator_org_id` | 运营控制（查看/使用/配置） | 客户租用 Atlas 设备，客户为 Operator |
| **Maintainer** | `maintainer_org_id` | 维护权限（查看/维修/状态更新） | 供应商为客户设备提供维保服务 |

### 5.2 授权关系示例

| 场景 | owner_org_id | operator_org_id | maintainer_org_id | 说明 |
| --- | --- | --- | --- | --- |
| Atlas 自有机房设备 | Atlas | NULL | NULL | 完全控制 |
| 客户租用 Atlas 设备 | Atlas | Customer A | Atlas | Atlas 拥有，Customer A 使用，Atlas 维保 |
| 客户自有设备委托维保 | Customer B | Customer B | Vendor X | Customer B 拥有并使用，Vendor X 维保 |

---

## 6. Resource Scope 与 Management Scope 的区别与组合判定

### 6.1 两个概念的区别

| 概念 | 定义 | 存储位置 | 作用 |
| --- | --- | --- | --- |
| **Resource Scope** | 用户可访问的数据范围 | 通过用户-组织关系 + 授权表计算 | 回答"用户能看到哪些对象" |
| **Management Scope** | 对象固有的管理能力边界 | `objects.management_scope` 字段 | 回答"这个对象允许什么级别的操作" |

### 6.2 权限判定组合逻辑

**权限通过 = 用户有操作权限 AND 对象在用户资源范围内 AND 操作不超过对象 management_scope**

伪代码：

```python
def check_permission(user, action, object):
    # 1. 用户有操作权限（基于角色）
    if not user.has_permission(action, resource_type='OBJECT'):
        return False
    
    # 2. 对象在用户资源范围内
    if not is_object_in_user_scope(user, object):
        return False
    
    # 3. 操作不超过对象 management_scope
    if not is_action_allowed_by_management_scope(action, object.management_scope):
        return False
    
    return True

def is_action_allowed_by_management_scope(action, management_scope):
    """
    management_scope 约束：
    - FULL_CONTROL: 允许所有操作
    - HARDWARE_ONLY: 允许硬件维护操作（MAINTAIN/VIEW），禁止 OS/应用操作
    - MAINTENANCE_ONLY: 仅允许 MAINTAIN 操作，禁止 EDIT/DELETE
    - NO_ACCESS: 禁止所有操作
    """
    if management_scope == 'FULL_CONTROL':
        return True
    if management_scope == 'HARDWARE_ONLY':
        return action in ['VIEW', 'MAINTAIN']
    if management_scope == 'MAINTENANCE_ONLY':
        return action == 'MAINTAIN'
    if management_scope == 'NO_ACCESS':
        return False
```

### 6.3 示例场景

| 场景 | 用户角色 | 对象 management_scope | 操作 | 判定 | 说明 |
| --- | --- | --- | --- | --- | --- |
| Atlas 工程师维护自有设备 | OPERATION_ENGINEER | FULL_CONTROL | MAINTAIN | ✅ | 通过 |
| 客户查看租用设备配置 | CUSTOMER_VIEWER | HARDWARE_ONLY | VIEW | ✅ | 通过 |
| 客户尝试修改租用设备 OS | CUSTOMER_ADMIN | HARDWARE_ONLY | EDIT | ❌ | management_scope 不允许 |
| 供应商尝试查看商业资产信息 | VENDOR_ENGINEER | MAINTENANCE_ONLY | VIEW_ASSET | ❌ | 无 VIEW_ASSET 权限 |

---

## 7. 用户资源授权关系设计

### 7.1 user_resource_grants 表设计

**该表定义见 docs/12 v0.2**

该表用于显式授权用户访问特定组织或对象集合，支持跨组织授权场景。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 授权记录唯一标识 |
| user_id | UUID | FK, NOT NULL | 用户（FK to users） |
| grant_type | VARCHAR(50) | NOT NULL | 授权类型（ORGANIZATION/OBJECT_SET） |
| target_org_id | UUID | FK, NULL | 目标组织（FK to organizations） |
| object_filters | JSONB | NULL | 对象过滤条件（如 {"object_type": "GPU", "location": "DC1"}） |
| access_level | VARCHAR(50) | NOT NULL | 访问级别（VIEW/EDIT/MAINTAIN） |
| granted_by | UUID | FK, NOT NULL | 授权人（FK to users） |
| granted_at | TIMESTAMP | NOT NULL | 授权时间 |
| expires_at | TIMESTAMP | NULL | 过期时间（NULL 表示永久） |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**索引**：
- `idx_user_resource_grants_user ON (user_id, grant_type)`
- `idx_user_resource_grants_org ON (target_org_id) WHERE grant_type='ORGANIZATION'`

### 7.2 跨组织授权示例

**场景**：用户属于组织 A，被授予组织 B 部分资源的查看权限。

```sql
-- 用户 Alice 属于 Atlas 组织
INSERT INTO users (id, username, organization_id) VALUES
  ('user-alice', 'alice', 'org-atlas');

-- 授予 Alice 查看 Customer B 的 GPU 资源
INSERT INTO user_resource_grants (user_id, grant_type, target_org_id, object_filters, access_level, granted_by)
VALUES (
  'user-alice',
  'ORGANIZATION',
  'org-customer-b',
  '{"object_type": "GPU"}',
  'VIEW',
  'user-admin'
);
```

查询 Alice 可访问的对象：

```sql
SELECT o.* FROM objects o
WHERE (
  -- 用户所属组织拥有的资源
  o.owner_org_id = (SELECT organization_id FROM users WHERE id = 'user-alice')
  OR o.operator_org_id = (SELECT organization_id FROM users WHERE id = 'user-alice')
  -- 或显式授权的组织资源
  OR EXISTS (
    SELECT 1 FROM user_resource_grants g
    WHERE g.user_id = 'user-alice'
      AND g.target_org_id IN (o.owner_org_id, o.operator_org_id, o.maintainer_org_id)
      AND (g.expires_at IS NULL OR g.expires_at > NOW())
      AND (g.object_filters IS NULL OR o.object_type_id IN (
        SELECT id FROM object_types WHERE name = g.object_filters->>'object_type'
      ))
  )
) AND o.deleted_at IS NULL;
```

---

## 8. 数据隔离查询规则

### 8.1 默认过滤规则

所有对象查询默认添加组织过滤条件：

```sql
SELECT * FROM objects
WHERE (
  owner_org_id IN (:user_accessible_orgs)
  OR operator_org_id IN (:user_accessible_orgs)
  OR maintainer_org_id IN (:user_accessible_orgs)
)
AND deleted_at IS NULL;
```

其中 `:user_accessible_orgs` 包括：

1. 用户所属组织（`users.organization_id`）
2. 用户显式授权的组织（`user_resource_grants.target_org_id`）
3. 用户所属组织的子组织（如果启用层级组织）

### 8.2 查询示例

**示例 1：Atlas 工程师查看自有设备**

```sql
-- 用户属于 Atlas 组织
SELECT o.* FROM objects o
WHERE o.owner_org_id = 'org-atlas'
  AND o.deleted_at IS NULL;
```

**示例 2：客户查看租用设备**

```sql
-- 客户 A 用户查看租用的设备
SELECT o.* FROM objects o
WHERE o.operator_org_id = 'org-customer-a'
  AND o.deleted_at IS NULL;
```

**示例 3：供应商查看维保设备**

```sql
-- 供应商 X 工程师查看维保设备
SELECT o.* FROM objects o
WHERE o.maintainer_org_id = 'org-vendor-x'
  AND o.deleted_at IS NULL;
```

**示例 4：跨组织授权查询**

```sql
-- Alice 查看所有可访问对象（包括跨组织授权）
WITH user_orgs AS (
  SELECT organization_id FROM users WHERE id = 'user-alice'
  UNION
  SELECT target_org_id FROM user_resource_grants
  WHERE user_id = 'user-alice'
    AND (expires_at IS NULL OR expires_at > NOW())
)
SELECT o.* FROM objects o
WHERE (
  o.owner_org_id IN (SELECT * FROM user_orgs)
  OR o.operator_org_id IN (SELECT * FROM user_orgs)
  OR o.maintainer_org_id IN (SELECT * FROM user_orgs)
)
AND o.deleted_at IS NULL;
```

### 8.3 应用层实现建议

- **ORM 全局过滤器**：在 SQLAlchemy/Django ORM 中配置全局过滤器，自动注入组织过滤条件
- **中间件拦截**：在 API 中间件层注入 `user_accessible_orgs`，避免每个接口重复编写
- **性能优化**：为 `owner_org_id`/`operator_org_id`/`maintainer_org_id` 创建联合索引

---

## 9. 与 docs/12 数据库表的对齐

### 9.1 已对齐的表

- **organizations 表**：支持 `org_type`（INTERNAL/CUSTOMER/VENDOR）和 `parent_org_id`
- **users 表**：关联 `organization_id`
- **roles 表**：支持全局角色和组织级角色（`organization_id` 可为 NULL）
- **permissions 表**：定义 `resource_type` 和 `action`
- **user_roles 表**：用户-角色关联
- **role_permissions 表**：角色-权限关联
- **audit_logs 表**：记录敏感操作的审计日志

### 9.2 待补充的表

- **user_resource_grants 表**：见 7.1 节设计，该表定义见 docs/12 v0.2

---

## 10. 审计与 MVP

敏感操作必须记录用户、时间、操作、对象、修改前和修改后数据。第一阶段实现用户、角色、基础权限和数据范围；后续实现多组织、客户隔离、供应商访问和细粒度资源策略。
