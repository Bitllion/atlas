# Atlas 开发任务拆解与 Codex 执行计划

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | 开发执行规划文档 |

## 1. 开发原则

采用增量开发和验收驱动开发，禁止一次性生成完整系统：

```text
工程基础 → Core 模型 → 业务模块 → 前端页面 → 数据采集 → 智能能力
```

## 2. 阶段任务拆解

> **本文档为阶段定义唯一权威**。docs/11 与 docs/18 的阶段描述应对齐本文档。

### 设计原则

- **依赖优先**：数据接入层（Phase 2）必须在 Asset（Phase 3）之前，因为 Asset 需要批量导入能力
- **端到端可验收**：每个 Phase 必须包含后端 API + 前端页面 + 数据库迁移 + 测试，确保功能完整可演示
- **增量交付**：Phase 1 交付 Object Explorer，Phase 3 交付 Asset 页面，Phase 4 交付 Operations 页面，Phase 5 交付 Dashboard

### Phase 0: 工程初始化

**✅ 状态**：已完成（main, 2026-09-04, 见 commit 7d68bc7）

**优先级**：P0（Infrastructure Core）

**目标**：建立项目骨架，确保前后端可启动、数据库可连接、迁移框架可用。

**交付物**：

- 仓库结构：`backend/`、`frontend/`、`database/`、`docker/`、`docs/`、`scripts/`、`tests/`
- 后端脚手架：Python 3.12 + FastAPI + SQLAlchemy + Alembic + PostgreSQL
- 前端脚手架：Vue 3 + TypeScript + Vue Router + Axios
- Docker Compose：启动 PostgreSQL、Backend、Frontend
- 配置管理：`config.py`（环境变量、数据库 URL、日志配置）
- 健康检查接口：`GET /health` 返回 `{"status":"ok"}`

**验收标准**：

- `docker-compose up` 启动所有服务
- `curl http://localhost:8000/health` 返回 `{"status":"ok"}`
- `curl http://localhost:8000/docs` 显示 Swagger UI
- 前端访问 `http://localhost:3000` 显示欢迎页面
- Alembic 迁移框架可执行 `alembic upgrade head`

**依赖**：无

---

### Phase 1: Infrastructure Core + Object Explorer

**✅ 状态**：已完成（main, 2026-09-04, 见 commit dc84a6a）

**优先级**：P0（Infrastructure Core）

**目标**：实现对象模型 CRUD API 与 Object Explorer 前端页面，建立 Atlas 数字化基础设施核心。

**交付物**：

**后端 API**：
- `POST /api/v1/objects`：创建对象
- `GET /api/v1/objects`：查询对象列表（支持按类型、状态、名称筛选）
- `GET /api/v1/objects/{id}`：获取对象详情
- `PUT /api/v1/objects/{id}`：更新对象
- `DELETE /api/v1/objects/{id}`：软删除对象
- `POST /api/v1/relationships`：创建关系
- `GET /api/v1/relationships`：查询关系（支持按 source/target 筛选）
- `GET /api/v1/object-types`：获取对象类型列表
- `GET /api/v1/objects/{id}/history`：获取对象历史记录

**数据库迁移（首批表）**：
- Core 域：`objects`、`object_types`、`object_specs`、`relationships`、`relationship_types`、`object_history`
- 权限域：`users`、`roles`、`permissions`、`organizations`、`user_roles`、`role_permissions`
- 治理域：`idempotency_keys`、`audit_logs`

详见 `docs/12-Atlas数据库模型设计.md` v0.2 中的字段定义。

**前端页面**：
- Object Explorer 列表页：展示对象列表（Name、Type、Status、Manufacturer、Serial Number）
- Object 详情页：展示基础信息、Specification（JSONB 渲染）、Relationships（关系图）、History（时间线）
- 对象创建/编辑表单

**初始化数据**：
- Object Types：`DATACENTER`、`ROOM`、`RACK`、`SERVER`、`GPU`、`NIC`、`CDU`、`POWER_SHELF`
- Relationship Types：`contains`、`installed_in`、`connected_to`、`feeds`、`powered_by`

**验收标准**：

- 能通过 API 创建 GB300 Rack（RACK 类型）
- 能通过 API 创建 Compute Tray（SERVER 类型）
- 能通过 API 创建 B300 GPU（GPU 类型）并设置 spec_data（model、memory、firmware、pci_bdf）
- 能通过 API 创建 BF3 NIC（NIC 类型）
- 能创建关系：GPU `installed_in` Server、Server `installed_in` Rack
- Object Explorer 页面能展示对象列表
- Object 详情页能展示基础信息、规格、关系图、历史记录
- 修改对象后，`object_history` 表记录 before/after 数据

**依赖**：Phase 0

---

### Phase 2: 数据接入层

**✅ 状态**：已完成（main, 2026-09-04, 见 commit 392ee4c）

**优先级**：P1（Asset Management 依赖）

**目标**：实现批量导入能力，支持 Excel/CSV 导入设备清单，为 Asset 模块准备数据。

**交付物**：

**后端 API**：
- `POST /api/v1/import/preview`：上传文件，返回导入预览（dry_run 模式，不写库）
- `POST /api/v1/import/execute`：执行导入（基于 preview 返回的 import_id）
- `GET /api/v1/import/history`：查询导入历史
- `GET /api/v1/import/{id}/errors`：查询导入错误详情

**数据库迁移**：
- `import_jobs`：导入任务记录（文件名、行数、成功/失败数、状态、错误摘要）
- `import_errors`：导入错误详情（行号、字段、错误类型、错误消息）

**功能特性**：
- 支持 Excel（.xlsx）、CSV 格式
- 支持批量创建对象与关系
- 重复检测（按 serial_number 或 name 去重）
- 字段验证（必填项、枚举值、外键引用）
- 错误反馈（行号、字段、错误原因）
- 事务保证（全部成功或全部回滚）

**前端页面**：
- 导入页面：上传文件 → 预览结果（成功/失败统计、错误列表）→ 确认导入
- 导入历史页面：展示导入记录与错误详情

**验收标准**：

- 能上传包含 100 台服务器的 Excel 文件
- 预览模式能返回验证结果（成功 95 条、失败 5 条，展示错误原因）
- 修正错误后能成功导入所有设备
- 导入后 Object Explorer 能查看导入的对象
- 导入历史记录在 `import_jobs` 表可查

**依赖**：Phase 1（依赖 Object API）

---

### Phase 3: Asset Management

**✅ 状态**：已完成（main, 2026-09-04, 见 commit 0b546d3）

**优先级**：P1（Asset Management）

**目标**：实现资产全生命周期管理，包括采购申请、验收、入库、部署、资产台账。

**交付物**：

**后端 API**：
- `POST /api/v1/purchases`：创建采购申请
- `PUT /api/v1/purchases/{id}/approve`：批准采购
- `POST /api/v1/assets`：创建资产记录（到货验收）
- `PUT /api/v1/assets/{id}/stock`：入库
- `PUT /api/v1/assets/{id}/deploy`：部署
- `GET /api/v1/assets`：查询资产列表（支持按状态、组织、位置筛选）
- `GET /api/v1/assets/{id}`：获取资产详情
- `GET /api/v1/assets/{id}/lifecycle`：获取资产生命周期事件

**数据库迁移**：
- `assets`：资产主表（关联 object_id、lifecycle_status、purchase_info、warranty_info、owner/operator/maintainer）
- `purchases`：采购申请表（申请人、审批人、预算、供应商、采购明细）
- `inventory_locations`：库存位置表（仓库、货架、位置编码）
- `deployments`：部署记录表（部署时间、部署位置、部署工程师、部署验收）

**前端页面**：
- 采购申请页面：创建采购申请、填写设备清单、提交审批
- 资产台账页面：展示资产列表（资产编号、设备名称、状态、所有者、位置）
- 库存管理页面：入库/出库操作、库存位置查看
- 资产详情页面：展示生命周期事件（采购 → 到货 → 入库 → 部署 → 使用中）

**验收标准**：

- 能创建采购申请（申请 10 台 GB300 服务器）
- 能批准采购申请
- 能批量创建资产记录（到货验收）
- 能批量入库（指定库存位置）
- 能将资产部署到机柜（指定 Rack）
- 资产状态自动流转：REQUESTED → APPROVED → ORDERED → RECEIVED → STOCK → DEPLOYED → ACTIVE
- 资产台账页面能按状态筛选（库存中、已部署、使用中）
- 资产详情页展示完整生命周期时间线

**依赖**：Phase 2（依赖批量导入能力）

---

### Phase 4: Operations Management

**✅ 状态**：已完成（main, 2026-09-04, 见 commit 327759f）

**优先级**：P2（Basic Operations）

**目标**：实现工单、故障、维修管理，支持运维基础流程。

**交付物**：

**后端 API**：
- `POST /api/v1/work-orders`：创建工单
- `PUT /api/v1/work-orders/{id}/assign`：分配工单
- `PUT /api/v1/work-orders/{id}/complete`：完成工单
- `GET /api/v1/work-orders`：查询工单列表（支持按状态、类型、优先级筛选）
- `POST /api/v1/faults`：创建故障记录
- `POST /api/v1/repairs`：创建维修记录
- `POST /api/v1/component-replacements`：记录部件更换
- `GET /api/v1/work-orders/{id}/timeline`：获取工单时间线

**数据库迁移**：
- `work_orders`：工单表（类型、优先级、状态、关联对象、创建人、处理人、描述）
- `faults`：故障表（故障类型、严重程度、故障现象、关联工单）
- `repairs`：维修记录表（维修工程师、维修时间、维修内容、关联工单）
- `component_replacements`：部件更换表（被替换部件、新部件、更换原因、关联维修记录）

**前端页面**：
- 工单列表页：展示工单列表（工单号、类型、状态、优先级、创建时间、处理人）
- 工单详情页：展示工单信息、故障详情、维修记录、部件更换、状态流转时间线
- 工单创建页面：选择设备 → 填写故障现象 → 设置优先级 → 提交工单
- 维修记录页面：记录维修过程、更换部件、上传维修照片

**验收标准**：

- 能创建故障工单（GPU001 温度过高）
- 能分配工单给工程师
- 能记录维修过程（检查散热器、更换导热硅脂）
- 能记录部件更换（更换风扇模块）
- 能完成工单并关闭
- 工单状态自动流转：OPEN → ASSIGNED → IN_PROGRESS → RESOLVED → CLOSED
- 工单详情页展示完整处理时间线
- 能通过对象详情页查看该对象的所有工单历史

**依赖**：Phase 1（依赖 Object API）

---

### Phase 5: Dashboard 与 Knowledge

**✅ 状态**：已完成（main, 2026-09-04, 见 commit f4acaab）

**优先级**：P2（Dashboard）、P3（Knowledge）

**目标**：实现综合 Dashboard 与知识管理，汇总 Core/Asset/Operations 数据，提供全局视图。

**交付物**：

**后端 API**：
- `GET /api/v1/dashboard/overview`：获取 Dashboard 概览数据（设备统计、资产分布、工单趋势）
- `GET /api/v1/dashboard/assets`：获取资产统计（按状态、按类型、按组织）
- `GET /api/v1/dashboard/operations`：获取运维统计（工单数量、故障率、平均修复时间）
- `POST /api/v1/knowledge/articles`：创建知识文章
- `POST /api/v1/knowledge/articles/{id}/attachments`：上传附件
- `POST /api/v1/knowledge/articles/{id}/link-objects`：关联对象
- `GET /api/v1/search`：全局搜索（按名称、SN、型号、标签）

**数据库迁移**：
- `knowledge_articles`：知识文章表（标题、内容、分类、标签、创建人）
- `article_attachments`：附件表（文件名、文件路径、文件大小）
- `article_object_links`：文章对象关联表（article_id、object_id）

**前端页面**：
- Dashboard：展示卡片（设备总数、资产状态分布、工单趋势图、故障 Top 5）
- Knowledge 列表页：展示知识文章列表（标题、分类、创建时间）
- Knowledge 详情页：展示文章内容、附件、关联对象
- Knowledge 创建页面：富文本编辑器、上传附件、关联对象
- 全局搜索框：输入关键词 → 展示搜索结果（对象、资产、工单、知识文章）

**验收标准**：

- Dashboard 展示设备总数（按类型分布：100 台服务器、800 块 GPU、200 张网卡）
- Dashboard 展示资产状态分布（库存中 20 台、已部署 80 台、使用中 50 台）
- Dashboard 展示工单趋势图（本月新增 15 个、已解决 12 个、平均修复时间 4 小时）
- 能上传 SOP 文档并关联到设备类型（GPU 更换流程）
- 全局搜索能查找设备（按 SN、型号、名称）
- 搜索结果点击能跳转到详情页

**依赖**：Phase 1、Phase 3、Phase 4（依赖 Core/Asset/Operations 数据）

---

### Phase 6: Agent 采集（非 MVP 必须）

**❌ 状态**：未开始（非 MVP 范围，已预留接口）

**优先级**：P4（Automation）

**目标**：实现自动化数据采集，支持 Agent 定期采集服务器/GPU 信息并更新对象。

**交付物**：

**Agent 框架（Go）**：
- Agent 注册与心跳
- 采集任务调度
- 采集器插件系统（Redfish、IPMI、SNMP、nvidia-smi、lspci、dmidecode、ethtool）
- 采集数据上报（HTTP JSON API）
- 错误重试与日志上报

**后端 API**：
- `POST /api/v1/agents`：注册 Agent
- `PUT /api/v1/agents/{id}/heartbeat`：Agent 心跳
- `POST /api/v1/collection/submit`：提交采集数据
- `GET /api/v1/collection/jobs`：查询采集任务
- `GET /api/v1/collection/failures`：查询采集失败记录

**数据库迁移**：
- `agents`：Agent 注册表（agent_id、hostname、version、last_heartbeat）
- `collection_jobs`：采集任务表（agent_id、object_id、采集器类型、调度配置）
- `collection_failures`：采集失败记录表（job_id、失败时间、错误原因、重试次数）

**采集器实现**：
- Redfish：采集服务器硬件信息（CPU、内存、磁盘、网卡、固件版本）
- IPMI：采集传感器数据（温度、电压、风扇转速）
- nvidia-smi：采集 GPU 信息（型号、驱动版本、温度、利用率、功耗、显存）
- SNMP：采集交换机端口状态

**验收标准**：

- Agent 能注册到平台并保持心跳
- Agent 能定期采集服务器信息（每 5 分钟）
- 采集数据能自动更新对象 spec_data（GPU 温度、利用率）
- 采集失败能记录到 `collection_failures` 表并重试
- 对象详情页能查看最新采集时间与数据来源
- 采集历史记录在 `object_history` 表可查（data_source='agent'）

**依赖**：Phase 1（依赖 Object API）

---

## 3. Phase 间依赖关系

```text
Phase 0 (工程初始化)
    ↓
Phase 1 (Infrastructure Core + Object Explorer)
    ↓
    ├─→ Phase 2 (数据接入层)
    │       ↓
    │   Phase 3 (Asset Management)
    │
    └─→ Phase 4 (Operations Management)
            ↓
        Phase 5 (Dashboard 与 Knowledge) ← 依赖 Phase 3
            ↓
        Phase 6 (Agent 采集，可选)
```

**关键依赖说明**：

- Phase 2 必须在 Phase 3 之前：Asset 模块需要批量导入能力初始化资产数据
- Phase 5 必须在 Phase 3 和 Phase 4 之后：Dashboard 需要汇总 Asset 和 Operations 数据
- Phase 6 可独立开发：Agent 采集是增强功能，不阻塞 MVP 验收

## 4. Codex 执行规则

每次任务开始前，必须：

1. 阅读 `AGENTS.md`，理解 Codex 代理的职责边界
2. 阅读 `README.md`，理解 Atlas 的核心理念（Object First、Relationship Driven、History Based）
3. 阅读当前 Phase 相关的设计文档（docs/10-架构设计、docs/12-数据库模型、docs/04-资产管理、docs/05-运维管理）
4. 确认数据模型、API 边界、前端页面需求后再编码

**严格禁止的行为**：

- ❌ 创建 `gpu_table`、`server_table`、`nic_table` 等专用设备表（所有设备必须通过 `objects` 表建模）
- ❌ 未经确认擅自拆分微服务（MVP 阶段采用模块化单体）
- ❌ 未经确认更换数据库（必须使用 PostgreSQL）
- ❌ 未经确认修改核心模型（Object/Relationship/History 的表结构与字段定义）
- ❌ 超范围实现功能（如 AI Agent、自动修复、PXE、Firmware 自动升级）
- ❌ 跳过数据库迁移直接修改生产表结构
- ❌ 跳过 API 直接在前端写业务逻辑

**推荐的实现顺序**：

1. 数据库迁移（Alembic migration）
2. 数据模型（SQLAlchemy models）
3. Schema 定义（Pydantic schemas）
4. 业务逻辑（Service 层）
5. API 路由（FastAPI routers）
6. 前端页面（Vue 3 组件）
7. 单元测试与集成测试
8. 文档更新

**实际开发补充规则**（基于 Phase 0-5 经验）：

- **Codex 额度耗尽时切换 claude-code**：若 codex 配额用完，推荐切换到 `claude-code` 继续开发（保持上下文）
- **测试库自动隔离**：pytest 使用 `atlas_test` 数据库（`DATABASE_URL` 环境变量指定），与开发库 `atlas_dev` 隔离，避免测试污染开发数据
- **权限点补种**：新增权限点后，需在开发库执行 `seed_permissions.py` 幂等补种（已有不会重复插入）；种子数据用 `seed.py` 初始化
- **部署命令速查**：
  - 后端重启：`systemctl restart atlas-api`
  - 前端更新：`cd frontend && npm run build && cp -r dist /opt/atlas/web/`
  - 查看日志：`journalctl -u atlas-api -f`
- **数据库迁移流程**：
  1. 修改模型：`backend/app/models/*.py`
  2. 生成迁移：`cd backend && alembic revision --autogenerate -m "描述"`
  3. 检查迁移脚本：`backend/alembic/versions/xxx_描述.py`
  4. 执行迁移：`alembic upgrade head`（开发库和生产库都需执行）

## 5. 每个 Phase 的输出要求

完成每个 Phase 后，必须输出：

### 5.1 代码变更清单

```text
修改文件：
- backend/app/models/object.py
- backend/app/api/v1/objects.py
- frontend/src/views/ObjectExplorer.vue
- database/alembic/versions/001_create_objects.py

新增文件：
- backend/app/services/object_service.py
- backend/app/schemas/object.py
- frontend/src/components/ObjectDetail.vue
```

### 5.2 数据库变更说明

```text
新增表：
- objects (12 个字段)
- object_types (4 个字段)
- relationships (7 个字段)

新增索引：
- idx_objects_type_status (object_type_id, status)
- idx_relationships_source (source_object_id)
```

### 5.3 API 变更清单

```text
新增 API：
- POST /api/v1/objects
- GET /api/v1/objects
- GET /api/v1/objects/{id}
- PUT /api/v1/objects/{id}

API 文档：http://localhost:8000/docs
```

### 5.4 测试结果

```text
单元测试：
- test_create_object: PASSED
- test_get_object_list: PASSED
- test_create_relationship: PASSED

集成测试：
- 创建 GB300 Rack: PASSED
- 创建 GPU 并建立关系: PASSED
- 查看对象详情: PASSED

前端验收：
- Object Explorer 列表页: ✓
- Object 详情页: ✓
- 关系图展示: ✓
```

### 5.5 验收截图或操作步骤

```text
验收步骤：
1. 访问 http://localhost:3000/objects
2. 点击"创建对象"按钮
3. 选择类型 "RACK"，填写名称 "GB300-RACK-001"
4. 提交后在列表页看到新对象
5. 点击对象进入详情页，查看基础信息、规格、关系
```

### 5.6 下一步计划

```text
Phase 1 已完成，下一步：
- 进入 Phase 2: 数据接入层
- 需要实现 Excel/CSV 导入 API
- 预计交付时间：2 天
```

## 6. Git Commit 规范

每完成一个子任务，必须提交 Git commit，格式：

```text
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**：

- `feat`: 新功能
- `fix`: 修复 Bug
- `refactor`: 重构（不改变功能）
- `docs`: 文档更新
- `test`: 测试代码
- `chore`: 构建工具、依赖更新

**Scope 范围**：

- `core`: Infrastructure Core
- `asset`: Asset Management
- `ops`: Operations Management
- `dashboard`: Dashboard
- `knowledge`: Knowledge
- `agent`: Agent 采集
- `db`: 数据库迁移
- `api`: API 路由
- `ui`: 前端页面

**示例**：

```text
feat(core): implement object model and CRUD API

- Add Object, ObjectType, ObjectSpec models
- Add Relationship, RelationshipType models
- Add Object History tracking
- Implement POST/GET/PUT/DELETE /api/v1/objects
- Add Alembic migration 001_create_core_tables

Closes #1
```

```text
feat(ui): implement Object Explorer page

- Add ObjectList component with filters
- Add ObjectDetail component with tabs
- Add RelationshipGraph component using D3.js
- Add object creation/edit form

Closes #2
```

## 7. 阶段验收 Checklist

每个 Phase 完成后，必须通过以下检查：

### Phase 0: 工程初始化

- [ ] `docker-compose up` 能启动所有服务
- [ ] `curl http://localhost:8000/health` 返回 `{"status":"ok"}`
- [ ] `curl http://localhost:8000/docs` 显示 Swagger UI
- [ ] 前端访问 `http://localhost:3000` 显示欢迎页面
- [ ] Alembic 迁移框架可执行 `alembic upgrade head`
- [ ] Git 已提交（commit message: `chore: initialize project structure`）

### Phase 1: Infrastructure Core + Object Explorer

- [ ] 能通过 API 创建 GB300 Rack
- [ ] 能通过 API 创建 Compute Tray、GPU、NIC
- [ ] 能创建关系：GPU `installed_in` Server
- [ ] Object Explorer 页面能展示对象列表
- [ ] Object 详情页能展示基础信息、规格、关系图、历史记录
- [ ] 修改对象后，`object_history` 表记录变更
- [ ] Swagger 文档已更新
- [ ] Git 已提交（至少 2 个 commit：`feat(core): ...` 和 `feat(ui): ...`）

### Phase 2: 数据接入层

- [ ] 能上传 Excel 文件并预览导入结果
- [ ] 预览模式能返回验证错误（行号、字段、错误原因）
- [ ] 能成功导入 100 台服务器
- [ ] 导入历史记录在 `import_jobs` 表可查
- [ ] 导入错误详情在 `import_errors` 表可查
- [ ] Git 已提交

### Phase 3: Asset Management

- [ ] 能创建采购申请并批准
- [ ] 能批量创建资产记录（到货验收）
- [ ] 能批量入库并指定库存位置
- [ ] 能将资产部署到机柜
- [ ] 资产状态能正确流转（REQUESTED → STOCK → DEPLOYED → ACTIVE）
- [ ] 资产台账页面能按状态筛选
- [ ] 资产详情页展示完整生命周期时间线
- [ ] Git 已提交

### Phase 4: Operations Management

- [ ] 能创建故障工单
- [ ] 能分配工单给工程师
- [ ] 能记录维修过程与部件更换
- [ ] 能完成工单并关闭
- [ ] 工单状态能正确流转（OPEN → ASSIGNED → IN_PROGRESS → RESOLVED → CLOSED）
- [ ] 工单详情页展示完整处理时间线
- [ ] 能通过对象详情页查看该对象的所有工单历史
- [ ] Git 已提交

### Phase 5: Dashboard 与 Knowledge

- [ ] Dashboard 展示设备总数与分布
- [ ] Dashboard 展示资产状态分布
- [ ] Dashboard 展示工单趋势图
- [ ] 能上传 SOP 文档并关联到设备
- [ ] 全局搜索能查找设备
- [ ] 搜索结果点击能跳转到详情页
- [ ] Git 已提交

### Phase 6: Agent 采集

- [ ] Agent 能注册到平台并保持心跳
- [ ] Agent 能定期采集服务器信息
- [ ] 采集数据能自动更新对象 spec_data
- [ ] 采集失败能记录并重试
- [ ] 对象详情页能查看最新采集时间
- [ ] Git 已提交

## 8. MVP 交付标准

### 8.1 MVP 定义

MVP（Minimum Viable Product）定义为 **Phase 0 ~ Phase 5** 的完整交付。Phase 6（Agent 采集）为增强功能，不属于 MVP 范围。

### 8.2 MVP 必达目标

MVP 必须能够：

1. **对象建模**：创建 GB300 Rack、Compute Tray、GPU、BF3 NIC、CDU、Power Shelf，建立 contains/installed_in/connected_to/powered_by 关系
2. **批量导入**：通过 Excel/CSV 批量导入 100+ 台设备清单
3. **资产管理**：完整走完采购申请 → 到货验收 → 入库 → 部署流程，查看资产生命周期
4. **运维管理**：创建故障工单 → 分配工程师 → 更换部件 → 关闭工单，查看维修记录
5. **Dashboard**：查看设备总数、资产状态分布、工单趋势，上传 SOP 并关联设备

### 8.3 MVP 页面清单

| 页面 | Phase | URL | 说明 |
| --- | --- | --- | --- |
| Object Explorer | Phase 1 | `/objects` | 对象列表、详情、关系图、历史记录 |
| 数据导入 | Phase 2 | `/import` | 上传 Excel/CSV、预览错误、执行导入 |
| Asset Management | Phase 3 | `/assets` | 采购流程、库存视图、资产台账 |
| Operations | Phase 4 | `/operations` | 工单流转、故障处理、维修记录 |
| Dashboard | Phase 5 | `/dashboard` | 设备统计、资产分布、工单趋势 |
| Knowledge | Phase 5 | `/knowledge` | 文档上传、分类、对象关联 |

### 8.4 MVP 验收演示脚本

**场景**：管理 AI 训练集群的基础设施生命周期

**步骤**：

1. **对象建模**（Phase 1）
   - 创建数据中心 DC001
   - 创建机柜 GB300-RACK-001
   - 创建 Compute Tray（8 台）
   - 创建 B300 GPU（64 块）、BF3 NIC（16 张）
   - 建立关系：GPU `installed_in` Compute Tray, Compute Tray `installed_in` Rack
   - 查看关系图，验证拓扑正确

2. **批量导入**（Phase 2）
   - 上传包含 100 台服务器的 Excel 清单
   - 预览导入结果（3 条错误：SN 重复）
   - 修正 Excel 后重新导入
   - 验证 Object Explorer 中新增 100 台服务器

3. **资产管理**（Phase 3）
   - 创建采购申请（50 台 GB300 服务器）
   - 批准采购申请
   - 到货验收（扫描 SN 批量创建资产记录）
   - 批量入库（指定仓库 A 货架 01）
   - 批量部署（选择 10 台部署到 Rack 001~010）
   - 查看资产台账，按状态筛选（库存中 40 台、已部署 10 台）

4. **运维管理**（Phase 4）
   - 发现 GPU001 温度异常，创建故障工单
   - 分配工单给工程师张三
   - 张三记录维修过程：检查散热器 → 更换导热硅脂 → 更换风扇模块
   - 记录部件更换：FAN-MODULE-001（旧）→ FAN-MODULE-002（新）
   - 完成工单并关闭
   - 查看 GPU001 的工单历史，验证维修记录完整

5. **Dashboard**（Phase 5）
   - 查看设备总数：100 台服务器、800 块 GPU、200 张 NIC
   - 查看资产状态分布：库存中 20%、已部署 60%、使用中 20%
   - 查看工单趋势：本月新增 15 个、已解决 12 个、平均修复时间 4 小时
   - 上传 SOP《GPU 更换流程》并关联到 GPU 类型
   - 搜索 "B300" 查找所有 B300 GPU

**验收通过标准**：演示脚本全程无阻塞，数据流转正确，页面操作流畅。

## 9. V2/V3/V4 规划

MVP 之后的版本规划（供参考，不属于当前开发范围）：

### V2: Agent 采集与监控（Phase 6）

- Go Agent 框架
- Redfish/IPMI/SNMP/nvidia-smi 采集器
- 定期采集与数据更新
- 采集失败告警

**价值**：减少手工录入，保持数据实时性。

### V3: Knowledge AI 与 RAG

- 文档向量化（Embedding）
- RAG 检索增强生成
- AI 助手（基于 LLM）
- 故障诊断建议

**价值**：智能化运维，快速查找 SOP 和历史案例。

### V4: Automation 与高级特性

- PXE 自动部署
- Firmware 自动升级
- 自动修复（基于 Workflow）
- 性能基线与异常检测

**价值**：全自动化运维，降低人工成本。
