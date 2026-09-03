# Atlas API 设计规范

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.2 |
| 状态 | API 设计文档 |

## 1. 原则

采用 RESTful API，Base URL 为 `/api/v1`。API 围绕领域资源、动作和状态转换设计，不按页面或具体硬件类型创建接口。

## 2. 全局约定

### 2.1 软删除语义

所有核心资源的 DELETE 操作执行**逻辑删除**，不物理删除数据：

- **DELETE** 操作将资源标记为已删除（设置 `deleted_at` 时间戳），响应 **204 No Content**
- 所有列表查询（GET collection）默认排除已删除资源（`WHERE deleted_at IS NULL`）
- 所有详情查询（GET resource）默认排除已删除资源，访问已删除资源返回 **404 Not Found**
- 恢复已删除资源需通过专用 API（如 `POST /api/v1/objects/{id}/restore`）

**示例**：
```http
DELETE /api/v1/objects/123e4567-e89b-12d3-a456-426614174000
→ 204 No Content

GET /api/v1/objects/123e4567-e89b-12d3-a456-426614174000
→ 404 Not Found
```

### 2.2 并发控制

支持乐观锁防止并发冲突，适用于 objects、assets、work_orders 等核心资源：

**请求方式**：
- **HTTP Header**：`If-Match: <version>` 或 `If-Match: "v<version>"`
- **Request Body**：`{"version": <version>, ...}`

**冲突响应**（409 Conflict）：
```json
{
  "error": "ConcurrentModificationError",
  "message": "资源已被修改，请刷新后重试",
  "current_version": 5,
  "expected_version": 3
}
```

**示例**：
```http
PUT /api/v1/objects/123e4567-e89b-12d3-a456-426614174000
If-Match: 3
Content-Type: application/json

{
  "name": "GPU-Node-001",
  "status": "MAINTENANCE"
}

→ 200 OK (成功更新，version 自动递增)
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "version": 4,
  ...
}

→ 409 Conflict (版本冲突)
```

### 2.3 幂等性

支持客户端提供 **Idempotency-Key** 防止重复请求（适用于 POST/PUT/DELETE）：

- **请求头**：`Idempotency-Key: <client-generated-uuid>`
- 相同幂等键的重复请求在 24 小时内返回首次响应（从 `idempotency_keys` 表读取缓存）
- 幂等键与请求体哈希（SHA256）绑定，请求体不同则拒绝（400 Bad Request）
- 幂等键过期时间为 24 小时，过期后自动清理

**存储表** (`idempotency_keys`)：
| 字段 | 说明 |
| --- | --- |
| idempotency_key | 客户端提供的幂等键 |
| endpoint | API 端点 |
| request_hash | 请求体 SHA256 哈希 |
| response_status | 首次响应状态码 |
| response_body | 首次响应体（JSONB） |
| expires_at | 过期时间（创建时间 + 24h） |

**示例**：
```http
POST /api/v1/purchase-requests
Idempotency-Key: a1b2c3d4-e5f6-4789-abcd-ef0123456789
Content-Type: application/json

{
  "title": "采购 10 台 H100 GPU",
  "quantity": 10
}

→ 201 Created (首次请求)
→ 201 Created (重复请求，返回缓存响应)
→ 400 Bad Request (相同幂等键但请求体不同)
```

## 3. Core API

### 3.1 对象管理

```http
GET    /api/v1/objects
POST   /api/v1/objects
GET    /api/v1/objects/{id}
PUT    /api/v1/objects/{id}
DELETE /api/v1/objects/{id}
GET    /api/v1/objects/{id}/spec
PUT    /api/v1/objects/{id}/spec
GET    /api/v1/objects/{id}/history
```

### 3.2 关系查询 API

```http
GET    /api/v1/objects/{id}/relations
GET    /api/v1/relationships
POST   /api/v1/relationships
DELETE /api/v1/relationships/{id}
```

**关系查询参数**（`GET /api/v1/objects/{id}/relations`）：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `depth` | int | 1 | 查询深度，范围 1-10。超出范围返回 422 或自动截断至最大值 |
| `relation_types` | string | (all) | 过滤关系类型，逗号分隔，如 `contains,installed_in` |
| `page` | int | 1 | 分页页码（从 1 开始） |
| `page_size` | int | 50 | 每页数量，范围 1-200 |

**环路保护**：
- 关系查询采用**深度优先遍历**，内置环路检测机制
- 检测到环路时停止遍历该分支，避免无限递归
- 响应中标记环路节点：`"has_cycle": true`

**示例**：
```http
GET /api/v1/objects/rack-001/relations?depth=2&relation_types=contains,powered_by&page=1&page_size=50

Response 200 OK:
{
  "object_id": "rack-001",
  "depth": 2,
  "relations": [
    {
      "relation_type": "contains",
      "target_object": {
        "id": "server-001",
        "name": "GPU-Server-001",
        "relations": [
          {
            "relation_type": "contains",
            "target_object": {"id": "gpu-001", "name": "H100-001"},
            "has_cycle": false
          }
        ]
      }
    },
    {
      "relation_type": "powered_by",
      "target_object": {"id": "pdu-001", "name": "PDU-A1"},
      "has_cycle": false
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 45,
    "total_pages": 1
  }
}
```

## 4. 业务与集成 API

### 4.1 资产管理

```http
GET/POST /api/v1/assets
GET/POST /api/v1/purchase-requests
GET/POST /api/v1/purchase-orders
POST     /api/v1/inventory/receive
POST     /api/v1/inventory/ship
GET/POST /api/v1/deployments
```

### 4.2 运维管理

```http
GET/POST /api/v1/work-orders
POST     /api/v1/work-orders/{id}/transition
GET/POST /api/v1/faults
GET/POST /api/v1/repairs
```

### 4.3 审批 API

#### 采购申请审批

**批准采购申请**

```http
POST /api/v1/purchase-requests/{id}/approve
Content-Type: application/json

Request:
{
  "comment": "已确认预算，批准采购",
  "approved_by": "user-uuid",
  "workflow_task_id": "task-uuid"  // 关联的工作流任务 ID
}

Response 200 OK:
{
  "id": "pr-uuid",
  "status": "APPROVED",
  "approved_by": "user-uuid",
  "approved_at": "2026-09-03T10:30:00Z",
  "workflow_task": {
    "id": "task-uuid",
    "status": "COMPLETED",
    "decision": "APPROVED"
  }
}
```

**拒绝采购申请**

```http
POST /api/v1/purchase-requests/{id}/reject
Content-Type: application/json

Request:
{
  "rejection_reason": "预算不足，建议下季度重新申请",  // 必填
  "rejected_by": "user-uuid",
  "workflow_task_id": "task-uuid"
}

Response 200 OK:
{
  "id": "pr-uuid",
  "status": "REJECTED",
  "rejected_by": "user-uuid",
  "rejected_at": "2026-09-03T10:35:00Z",
  "rejection_reason": "预算不足，建议下季度重新申请",
  "workflow_task": {
    "id": "task-uuid",
    "status": "COMPLETED",
    "decision": "REJECTED"
  }
}
```

#### 工单审批

```http
POST /api/v1/work-orders/{id}/approve
POST /api/v1/work-orders/{id}/reject
```

请求/响应格式与采购申请审批类似，均需关联 `workflow_task_id` 并记录审批意见。

### 4.4 导入 API

```http
POST /api/v1/import
```

**批量导入资源**（支持 objects、assets、relationships 等）

**请求参数**：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `resource_type` | string | 必填 | 资源类型（objects/assets/relationships） |
| `dry_run` | boolean | false | 预检模式，不实际写入数据库，仅验证数据格式与约束 |
| `on_conflict` | string | error | 冲突策略：`skip`（跳过冲突行）、`update`（更新已存在记录）、`error`（遇冲突中止） |

**请求体**：
```json
{
  "resource_type": "objects",
  "dry_run": false,
  "on_conflict": "update",
  "data": [
    {"serial_number": "SN001", "name": "GPU-001", ...},
    {"serial_number": "SN002", "name": "GPU-002", ...}
  ]
}
```

**响应格式**：
```json
{
  "success_count": 8,
  "failed_count": 2,
  "total_count": 10,
  "errors": [
    {
      "row": 3,
      "field": "serial_number",
      "message": "序列号已存在且 on_conflict=error"
    },
    {
      "row": 7,
      "field": "object_type_id",
      "message": "对象类型不存在"
    }
  ],
  "dry_run": false
}
```

**事务语义**：

本 API 采用**部分成功模式**（逐行处理）：
- 每行独立处理，单行失败不影响其他行的成功导入
- 失败行记录在 `errors` 数组中，成功行正常写入数据库
- 适用于大批量导入场景，最大化数据导入成功率

**备注**：如需**全部成功或全部回滚**的原子性语义，请在请求中添加 `atomic: true` 参数（后续版本支持）。

### 4.5 知识管理

```http
GET/POST /api/v1/knowledge
```

### 4.6 数据采集

```http
POST /api/v1/agents/register
POST /api/v1/agents/report
```

### 4.7 审计日志查询

```http
GET /api/v1/audit-logs
```

**查询参数**：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `user_id` | UUID | 按操作用户过滤 |
| `action` | string | 按操作类型过滤（CREATE/UPDATE/DELETE/APPROVE/TRANSFER/LOGIN） |
| `resource_type` | string | 按资源类型过滤（OBJECT/ASSET/WORK_ORDER/USER/ROLE） |
| `resource_id` | UUID | 按资源 ID 过滤 |
| `start_time` | ISO8601 | 起始时间（闭区间） |
| `end_time` | ISO8601 | 结束时间（开区间） |
| `page` | int | 分页页码（默认 1） |
| `page_size` | int | 每页数量（默认 50，最大 200） |

**示例**：
```http
GET /api/v1/audit-logs?user_id=user-123&action=UPDATE&resource_type=ASSET&start_time=2026-09-01T00:00:00Z&end_time=2026-09-04T00:00:00Z&page=1&page_size=50

Response 200 OK:
{
  "logs": [
    {
      "id": "log-uuid",
      "user_id": "user-123",
      "action": "UPDATE",
      "resource_type": "ASSET",
      "resource_id": "asset-456",
      "before_data": {"status": "STOCK"},
      "after_data": {"status": "DEPLOYED"},
      "ip_address": "192.168.1.100",
      "created_at": "2026-09-03T14:23:45Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 127,
    "total_pages": 3
  }
}
```

## 5. 权限与版本

所有 API 经过 Authentication、Authorization、Resource Scope 和 Management Scope。客户只能访问授权资源；接口升级使用 `/api/v2`，不得破坏旧版本。

## 6. 错误码总表

| 状态码 | 说明 | 适用场景 |
| --- | --- | --- |
| **400 Bad Request** | 请求参数错误 | 缺少必填字段、字段类型错误、参数格式不正确、幂等键冲突（相同键但请求体不同） |
| **401 Unauthorized** | 未认证 | 缺少认证凭证、Token 过期或无效 |
| **403 Forbidden** | 无权限 | 用户已认证但无权访问该资源、跨组织访问被拒绝、操作超出 Management Scope |
| **404 Not Found** | 资源不存在 | 资源 ID 不存在、资源已被软删除（`deleted_at` 不为空） |
| **409 Conflict** | 资源冲突 | 并发修改冲突（乐观锁版本不匹配）、唯一约束冲突（如 serial_number 重复）、状态转换不合法 |
| **422 Unprocessable Entity** | 语义错误 | 业务逻辑验证失败（如关系类型不允许、查询深度超出范围、工单状态机转换非法） |
| **429 Too Many Requests** | 请求过载 | API 调用频率超出限制 |
| **500 Internal Server Error** | 服务器内部错误 | 未预期的系统错误、数据库连接失败 |

**标准错误响应格式**：
```json
{
  "error": "ErrorCode",
  "message": "人类可读的错误描述",
  "details": {
    "field": "specific_field",
    "reason": "详细原因"
  },
  "timestamp": "2026-09-03T10:30:00Z",
  "request_id": "req-uuid"
}
```
