# Atlas API 设计规范

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | API 设计文档 |

## 1. 原则

采用 RESTful API，Base URL 为 `/api/v1`。API 围绕领域资源、动作和状态转换设计，不按页面或具体硬件类型创建接口。

## 2. Core API

```http
GET    /api/v1/objects
POST   /api/v1/objects
GET    /api/v1/objects/{id}
PUT    /api/v1/objects/{id}
DELETE /api/v1/objects/{id}
GET    /api/v1/objects/{id}/spec
PUT    /api/v1/objects/{id}/spec
GET    /api/v1/objects/{id}/history
GET    /api/v1/objects/{id}/relations
GET    /api/v1/relationships
POST   /api/v1/relationships
DELETE /api/v1/relationships/{id}
```

DELETE 实际执行逻辑退休或 inactive，不物理删除。

## 3. 业务与集成 API

```http
GET/POST /api/v1/assets
GET/POST /api/v1/purchase-requests
POST     /api/v1/purchase-requests/{id}/approve
POST     /api/v1/inventory/receive
POST     /api/v1/inventory/ship
GET/POST /api/v1/deployments
GET/POST /api/v1/work-orders
POST     /api/v1/work-orders/{id}/transition
GET/POST /api/v1/faults
GET/POST /api/v1/repairs
GET/POST /api/v1/knowledge
POST     /api/v1/agents/register
POST     /api/v1/agents/report
POST     /api/v1/import
GET      /api/v1/audit-logs
```

## 4. 权限与版本

所有 API 经过 Authentication、Authorization、Resource Scope 和 Management Scope。客户只能访问授权资源；接口升级使用 `/api/v2`，不得破坏旧版本。
