# Atlas MVP 数据库初始化与第一批开发任务

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | 开发执行文档 |

## 1. 文档目的

本文档用于指导 Atlas MVP 第一阶段开发。

目标：

- 完成项目初始化
- 完成数据库初始化
- 完成 Infrastructure Core 的第一版实现

## 2. Codex 启动要求

执行任何代码前，必须阅读：

- `AGENTS.md`
- `README.md`
- `docs/`

必须理解：Atlas 的核心不是传统资产系统，而是基础设施数字化模型。

第一阶段必须遵循：

- Object First：对象优先
- Relationship Driven：关系驱动
- History Based：历史可追踪

## 3. 第一阶段目标：Atlas Core

第一阶段完成以下核心能力：

- Object
- Object Type
- Specification
- Relationship
- History

完成后，Atlas 应能够描述：

- Data Center
- Rack
- Server
- GPU
- NIC
- CDU

## 4. 初始化工程

项目目录应包含：

```text
atlas-platform/
├── backend/
├── frontend/
├── database/
├── docker/
├── docs/
├── scripts/
└── tests/
```

## 5. Backend 初始化

默认技术栈：

- Python 3.12
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL

建议目录：

```text
backend/
└── app/
    ├── main.py
    ├── config/
    ├── database/
    ├── models/
    ├── schemas/
    ├── api/
    ├── services/
    └── core/
```

## 6. Docker 环境

创建 `docker-compose.yml`，至少支持启动：

- PostgreSQL
- Backend
- Frontend

## 7. 数据库初始化

创建数据库：

```text
atlas
```

数据库结构应通过 Alembic 管理，不应直接依赖手工修改生产数据库。

## 8. 第一批数据表

### 8.1 `object_types`

用途：定义对象类型。

字段：

- `id`
- `name`
- `description`
- `created_at`

初始化对象类型：

- `DATACENTER`
- `ROOM`
- `RACK`
- `SERVER`
- `GPU`
- `NIC`
- `CDU`
- `POWER_SHELF`

### 8.2 `objects`

字段：

- `id`
- `object_type_id`
- `name`
- `serial_number`
- `manufacturer`
- `model`
- `status`
- `created_at`
- `updated_at`

### 8.3 `object_specs`

字段：

- `id`
- `object_id`
- `spec_data`（JSONB）
- `created_at`
- `updated_at`

### 8.4 `relationship_types`

初始化关系类型：

- `contains`
- `installed_in`
- `connected_to`
- `feeds`
- `powered_by`

### 8.5 `relationships`

字段：

- `id`
- `source_object_id`
- `relationship_type_id`
- `target_object_id`
- `status`
- `created_at`

### 8.6 `object_history`

字段：

- `id`
- `object_id`
- `action`
- `before_data`
- `after_data`
- `operator`
- `created_at`

## 9. 第一阶段 API

### 9.1 Object API

创建：

```http
POST /api/v1/objects
```

查询：

```http
GET /api/v1/objects
```

详情：

```http
GET /api/v1/objects/{id}
```

更新：

```http
PUT /api/v1/objects/{id}
```

### 9.2 Relationship API

创建：

```http
POST /api/v1/relationships
```

查询：

```http
GET /api/v1/relationships
```

## 10. 第一批测试数据

### 10.1 数据中心

```text
DC001
```

### 10.2 机柜

```text
RACK001
```

关系：

```text
RACK001 --installed_in--> DC001
```

### 10.3 Server

```text
SERVER001
```

关系示例：

```text
SERVER001 --contains--> GPU001
```

### 10.4 GPU

```text
GPU001
```

规格示例：

```json
{
  "model": "B300",
  "memory": "288GB",
  "firmware": "97.xx",
  "pci_bdf": "41:00.0"
}
```

## 11. 前端第一页面

实现 `Object Explorer`。

列表展示：

- Name
- Type
- Status
- Manufacturer

详情页展示：

- Basic Info
- Specification
- Relationship
- History

## 12. 验收标准

### Backend

Backend 可以启动：

```bash
uvicorn app.main:app
```

访问 `/docs` 可以看到 Swagger API。

### Database

可以查询以下核心数据：

- `objects`
- `object_specs`
- `relationships`

### Frontend

- 可以查看对象列表
- 可以点击对象
- 可以查看对象详情

## 13. Codex 执行 Prompt

### 第一次执行

```text
你现在负责初始化 Atlas Platform 项目。

请严格遵守 AGENTS.md。
请先阅读 README.md 和 docs/。
不要编写业务代码。

第一步：完成项目目录初始化。
第二步：完成 backend/frontend/docker 基础工程。
第三步：输出修改文件列表和下一步计划。
```

### 第二次执行

```text
开始实现 Atlas Infrastructure Core。

要求实现：
- Object
- ObjectType
- Specification
- Relationship
- History

不要创建：
- GPU 表
- Server 表
- NIC 表

所有设备必须通过 Object 模型表达。

完成后输出：
- 修改文件
- 数据库变化
- API 列表
- 测试结果
```

## 14. 开发纪律

每完成一个阶段，必须提交 Git commit。

示例：

```text
feat(core): implement object model
```

提交前应确认：

- 文档已同步
- 数据库迁移可执行
- API 可访问
- 测试结果明确

## 15. 后续阶段

完成 Core 后，依次进入：

1. Asset Domain
2. Operations Domain
3. Knowledge
4. Agent
5. AI 能力

## 16. 阶段总结

第一阶段目标不是完成 Atlas 全部功能，而是建立：

```text
Atlas Digital Infrastructure Core
```

这是未来以下能力的基础：

- 资产管理
- 运维管理
- AI 助手
- 自动化能力

