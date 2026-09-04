# Atlas 开发进度与交接文档

| 项目 | 内容 |
| --- | --- |
| 文档版本 | v1.0 |
| 最后更新 | 2026-09-04 |
| 当前分支 | main（docs-progress 待合并） |
| 当前状态 | MVP Phase 0-5 已交付，Phase 6 未开始 |

---

## 1. 当前实现总览

### 1.1 按域列出模块与核心 API

**Infrastructure Core 域（基础设施核心）**

- **对象模型**（Object / ObjectType / ObjectSpec / ObjectHistory）
  - `POST /api/v1/objects` - 创建对象
  - `GET /api/v1/objects` - 查询对象列表（支持类型/状态/名称筛选）
  - `GET /api/v1/objects/{id}` - 获取对象详情
  - `PUT /api/v1/objects/{id}` - 更新对象
  - `DELETE /api/v1/objects/{id}` - 软删除对象
  - `GET /api/v1/objects/{id}/history` - 获取对象历史记录
  - `GET /api/v1/object-types` - 获取对象类型列表

- **关系模型**（Relationship / RelationshipType）
  - `POST /api/v1/relationships` - 创建关系
  - `GET /api/v1/relationships` - 查询关系（支持按 source/target 筛选）
  - `GET /api/v1/objects/{id}/relations` - 获取对象关系图

- **全局搜索**
  - `GET /api/v1/search` - 全局搜索（按名称/SN/型号/标签）

**Asset Management 域（资产管理）**

- **采购申请**（Purchase / PurchaseItem）
  - `POST /api/v1/purchases` - 创建采购申请
  - `GET /api/v1/purchases` - 查询采购列表
  - `GET /api/v1/purchases/{id}` - 获取采购详情
  - `POST /api/v1/workflow/processes/purchase_approval/start` - 启动采购审批流程

- **资产管理**（Asset / AssetLifecycleEvent）
  - `POST /api/v1/assets` - 创建资产记录（到货验收）
  - `PUT /api/v1/assets/{id}/stock` - 入库
  - `PUT /api/v1/assets/{id}/deploy` - 部署
  - `PUT /api/v1/assets/{id}/transfer` - 调拨
  - `PUT /api/v1/assets/{id}/retire` - 退役
  - `PUT /api/v1/assets/{id}/unretire` - 退役撤销
  - `GET /api/v1/assets` - 查询资产列表（支持状态/组织/位置筛选）
  - `GET /api/v1/assets/{id}` - 获取资产详情
  - `GET /api/v1/assets/{id}/lifecycle` - 获取资产生命周期事件

- **库存位置**（InventoryLocation）
  - `POST /api/v1/inventory-locations` - 创建库存位置
  - `GET /api/v1/inventory-locations` - 查询库存位置列表

- **部署记录**（Deployment）
  - `GET /api/v1/deployments` - 查询部署记录

**Operations Management 域（运维管理）**

- **工单**（WorkOrder / WorkOrderEvent）
  - `POST /api/v1/work-orders` - 创建工单
  - `PUT /api/v1/work-orders/{id}/assign` - 分配工单
  - `PUT /api/v1/work-orders/{id}/start` - 开始处理
  - `PUT /api/v1/work-orders/{id}/resolve` - 解决工单
  - `PUT /api/v1/work-orders/{id}/close` - 关闭工单
  - `PUT /api/v1/work-orders/{id}/reopen` - 重新打开
  - `GET /api/v1/work-orders` - 查询工单列表（支持状态/类型/优先级筛选）
  - `GET /api/v1/work-orders/{id}` - 获取工单详情
  - `GET /api/v1/work-orders/{id}/timeline` - 获取工单时间线

- **故障**（Fault）
  - `POST /api/v1/faults` - 创建故障记录
  - `GET /api/v1/faults` - 查询故障列表

- **维修**（Repair）
  - `POST /api/v1/repairs` - 创建维修记录
  - `GET /api/v1/repairs` - 查询维修列表

- **部件更换**（ComponentReplacement）
  - `POST /api/v1/component-replacements` - 记录部件更换
  - `GET /api/v1/component-replacements` - 查询更换记录

**Dashboard 域（仪表板）**

- `GET /api/v1/dashboard/overview` - 获取 Dashboard 概览（设备/资产/工单统计）
- `GET /api/v1/dashboard/assets` - 获取资产统计（按状态/类型/组织）
- `GET /api/v1/dashboard/operations` - 获取运维统计（工单数量/故障率/平均修复时间）
- `GET /api/v1/dashboard/charts/work-orders-trend` - 工单趋势图（按月）

**Knowledge Management 域（知识管理）**

- **知识文章**（KnowledgeArticle / ArticleAttachment / ArticleObjectLink）
  - `POST /api/v1/knowledge/articles` - 创建知识文章
  - `GET /api/v1/knowledge/articles` - 查询知识文章列表
  - `GET /api/v1/knowledge/articles/{id}` - 获取文章详情
  - `POST /api/v1/knowledge/articles/{id}/attachments` - 上传附件
  - `GET /api/v1/knowledge/attachments/{id}/download` - 下载附件
  - `POST /api/v1/knowledge/articles/{id}/link-objects` - 关联对象

- **知识 AI 问答**
  - `POST /api/v1/knowledge/ask` - 提问（支持 RAG 检索 + LLM 生成）
  - `GET /api/v1/knowledge/llm-configs` - 获取 LLM 配置列表
  - `POST /api/v1/knowledge/llm-configs` - 创建 LLM 配置

**Data Import 域（数据导入）**

- `POST /api/v1/import/preview` - 上传文件预览（dry_run 模式）
- `POST /api/v1/import/execute` - 执行导入
- `GET /api/v1/import/history` - 查询导入历史
- `GET /api/v1/import/{id}/errors` - 查询导入错误详情

**Workflow Engine 域（工作流引擎）**

- `POST /api/v1/workflow/processes` - 创建流程定义
- `GET /api/v1/workflow/processes` - 查询流程定义列表
- `POST /api/v1/workflow/processes/{key}/start` - 启动流程实例
- `GET /api/v1/workflow/instances` - 查询流程实例列表
- `GET /api/v1/workflow/instances/{id}` - 获取实例详情
- `GET /api/v1/workflow/tasks/my` - 获取我的待办任务
- `POST /api/v1/workflow/tasks/{id}/approve` - 批准任务
- `POST /api/v1/workflow/tasks/{id}/reject` - 驳回任务

**Notification System 域（通知系统）**

- `GET /api/v1/notifications/my` - 获取我的通知列表
- `GET /api/v1/notifications/my/unread-count` - 获取未读数
- `PUT /api/v1/notifications/{id}/read` - 标记已读
- `PUT /api/v1/notifications/read-all` - 全部标记已读

**Data Quality 域（数据质量）**

- `POST /api/v1/quality/rules` - 创建质量规则
- `GET /api/v1/quality/rules` - 查询质量规则列表
- `POST /api/v1/quality/rules/{id}/check` - 执行质量检查
- `GET /api/v1/quality/issues` - 查询质量问题列表
- `POST /api/v1/quality/issues/{id}/resolve` - 解决质量问题
- `GET /api/v1/quality/reports` - 查询质量报告列表

**Permission & Organization 域（权限与组织）**

- **用户**（User / UserRole）
  - `POST /api/v1/users` - 创建用户
  - `GET /api/v1/users` - 查询用户列表
  - `GET /api/v1/users/me` - 获取当前用户信息

- **角色**（Role / RolePermission）
  - `POST /api/v1/roles` - 创建角色
  - `GET /api/v1/roles` - 查询角色列表

- **权限**（Permission）18 个权限点
  - `objects:read` / `objects:write` - 对象读写
  - `assets:read` / `assets:write` - 资产读写
  - `work_orders:read` / `work_orders:write` - 工单读写
  - `knowledge:read` / `knowledge:write` - 知识读写
  - `imports:write` - 数据导入
  - `dashboard:read` - Dashboard 查看
  - `workflow:approve` - 工作流审批
  - `quality:read` / `quality:write` - 数据质量读写
  - `users:read` / `users:write` - 用户管理
  - `roles:read` / `roles:write` - 角色管理
  - `organizations:read` / `organizations:write` - 组织管理

- **组织**（Organization）
  - `POST /api/v1/organizations` - 创建组织
  - `GET /api/v1/organizations` - 查询组织列表

- **登录认证**
  - `POST /api/v1/auth/login` - 登录（JWT）
  - `POST /api/v1/auth/refresh` - 刷新 Token

**核心 API 统计**：
- 对象模型：7 个 API
- 关系模型：3 个 API
- 资产管理：12 个 API
- 运维管理：11 个 API
- Dashboard：4 个 API
- 知识管理：8 个 API
- 数据导入：4 个 API
- 工作流引擎：8 个 API
- 通知系统：4 个 API
- 数据质量：7 个 API
- 权限与组织：8 个 API
- **合计**：76+ API 端点

### 1.2 数据库表结构（27+ 表）

**Core 域**：
- `objects` - 对象主表（name/type/status/manufacturer/serial_number/spec_data/organization_id）
- `object_types` - 对象类型（DATACENTER/ROOM/RACK/SERVER/GPU/NIC/STORAGE/CDU/POWER_SHELF）
- `object_specs` - 对象规格（已废弃，使用 spec_data JSONB 字段）
- `relationships` - 关系表（source/target/type）
- `relationship_types` - 关系类型（contains/installed_in/connected_to/feeds/powered_by）
- `object_history` - 对象历史记录（before/after/change_type/changed_by/data_source）

**Asset 域**：
- `assets` - 资产主表（object_id/lifecycle_status/purchase_id/owner/operator/maintainer）
- `purchases` - 采购申请（requester/approver/status/total_budget/supplier/purchase_date）
- `purchase_items` - 采购明细（purchase_id/object_type/quantity/unit_price）
- `inventory_locations` - 库存位置（warehouse/rack/shelf/position）
- `deployments` - 部署记录（asset_id/deployed_at/deployed_by/location）
- `asset_lifecycle_events` - 资产生命周期事件（asset_id/event_type/event_time/operator）

**Operations 域**：
- `work_orders` - 工单表（type/priority/status/object_id/creator/assignee/description）
- `work_order_events` - 工单事件（work_order_id/event_type/event_time/operator）
- `faults` - 故障表（work_order_id/fault_type/severity/phenomenon）
- `repairs` - 维修记录（work_order_id/engineer/repair_time/repair_content）
- `component_replacements` - 部件更换（repair_id/old_component/new_component/reason）

**Dashboard 域**：
- 无独立表，通过 Core/Asset/Operations 表聚合统计

**Knowledge 域**：
- `knowledge_articles` - 知识文章（title/content/category/tags/author）
- `article_attachments` - 附件表（article_id/file_name/file_path/file_size）
- `article_object_links` - 文章对象关联（article_id/object_id）
- `llm_configs` - LLM 配置（name/provider/model_name/api_key/base_url/temperature）

**Data Import 域**：
- `import_jobs` - 导入任务（file_name/row_count/success_count/failed_count/status/error_summary）
- `import_errors` - 导入错误（import_job_id/row_number/field_name/error_type/error_message）

**Workflow Engine 域**：
- `workflow_process_definitions` - 流程定义（key/name/version/nodes/edges）
- `workflow_instances` - 流程实例（process_key/status/context/start_time/end_time）
- `workflow_tasks` - 任务表（instance_id/node_id/assignee/status/approve_comment）

**Notification System 域**：
- `notifications` - 通知表（user_id/type/title/content/related_entity_type/related_entity_id/is_read）

**Data Quality 域**：
- `quality_rules` - 质量规则（name/rule_type/target_type/condition/severity）
- `quality_issues` - 质量问题（rule_id/object_id/issue_type/description/severity/status）
- `quality_reports` - 质量报告（report_date/total_objects/issues_count/severe_issues_count）

**Permission & Organization 域**：
- `users` - 用户表（username/password_hash/full_name/email/is_active/organization_id）
- `roles` - 角色表（name/description）
- `permissions` - 权限表（code/name/category）
- `user_roles` - 用户角色关联（user_id/role_id）
- `role_permissions` - 角色权限关联（role_id/permission_id）
- `organizations` - 组织表（name/code/parent_id/description）

**治理域**：
- `idempotency_keys` - 幂等性键（key/table_name/record_id/created_at）
- `audit_logs` - 审计日志（user_id/action/table_name/record_id/old_value/new_value）

### 1.3 前端页面（13+ 页面）

| 页面路由 | 页面名称 | 功能 | 权限要求 |
| --- | --- | --- | --- |
| `/objects` | Object Explorer | 对象列表、详情、关系图、历史时间线 | objects:read |
| `/objects/:id` | Object Detail | 对象详情（基础信息/规格/关系/历史） | objects:read |
| `/assets` | Asset Management | 资产台账（采购/库存/部署/调拨/退役） | assets:read |
| `/purchase-requests` | Purchase Requests | 采购申请列表与创建 | assets:write |
| `/inventory` | Inventory | 库存管理 | assets:read |
| `/work-orders` | Work Orders | 工单列表、详情、时间线 | work_orders:read |
| `/work-orders/create` | Create Work Order | 创建工单 | work_orders:write |
| `/dashboard` | Dashboard | 设备/资产/工单统计（支持组织过滤） | dashboard:read |
| `/knowledge` | Knowledge Base | 知识文章列表与搜索 | knowledge:read |
| `/knowledge/create` | Create Article | 创建知识文章（富文本编辑器） | knowledge:write |
| `/knowledge/:id` | Article Detail | 文章详情（内容/附件/关联对象） | knowledge:read |
| `/knowledge/ai` | Knowledge AI | AI 问答（RAG + LLM） | knowledge:read |
| `/import` | Data Import | Excel/CSV 导入（上传/预览/执行） | imports:write |
| `/approvals` | My Approvals | 我的审批（待办任务列表） | workflow:approve |
| `/data-quality` | Data Quality | 数据质量中心（规则/问题/报告） | quality:read |
| `/users` | User Management | 用户管理 | users:read |
| `/organizations` | Organizations | 组织管理 | organizations:read |
| `/login` | Login | 登录页面（JWT 认证） | 无（公开） |

**前端特性**：
- **通知铃铛**（App.vue）：未读消息红点徽章 + 下拉通知列表 + 点击跳转
- **角色化显隐**：基于权限点的菜单/按钮显隐（`v-if="hasPermission('objects:write')"`)
- **全局搜索框**（App.vue）：搜索对象（按名称/SN/型号）
- **组织过滤器**（Dashboard）：支持按组织过滤统计数据

---

## 2. 测试与 CI

### 2.1 测试覆盖

**测试文件**（backend/tests/，共 20 个文件）：
- `test_objects.py` - 对象 CRUD 测试
- `test_relationships.py` - 关系创建与查询测试
- `test_assets.py` - 资产生命周期测试
- `test_work_orders.py` - 工单流转测试
- `test_dashboard.py` - Dashboard 统计测试
- `test_search.py` - 全局搜索测试
- `test_workflow.py` - 工作流引擎测试
- `test_notifications.py` - 通知系统测试
- `test_quality.py` - 数据质量测试
- `test_scope.py` - 组织读隔离测试
- `test_scope_write.py` - 组织写隔离测试
- 其他 9 个测试文件

**测试结果**：
- **65 passed**（单元测试 + 集成测试）
- **测试数据库**：`atlas_test`（与开发库 `atlas_dev` 隔离）
- **CI 自动化**：每次 push 到 main 或 PR 时自动运行 pytest

### 2.2 CI/CD 流水线

**GitHub Actions**（`.github/workflows/ci.yml`）：

```yaml
jobs:
  backend:
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_DB: atlas_test
    env:
      DATABASE_URL: postgresql+psycopg://atlas:atlas@localhost:5432/atlas_test
    steps:
      - pip install -r requirements.txt
      - alembic upgrade head
      - pytest

  frontend:
    steps:
      - npm ci
      - npm run build
```

**触发条件**：
- push 到 main 分支
- 创建 Pull Request

---

## 3. 部署架构

### 3.1 生产环境架构（文字描述）

```text
Internet
    ↓
nginx:80 (反向代理 + 静态文件)
    ├── /api/v1/* → atlas-api:8000 (FastAPI 后端)
    └── /* → /opt/atlas/web/dist (Vue 3 前端静态文件)
         ↓
    atlas-api:8000 (systemd 服务)
    gunicorn + uvicorn workers (4 workers)
         ↓
    PostgreSQL 17 (Docker 容器: atlas-dev-pg)
    - 端口: 55433 (宿主机) → 5432 (容器内)
    - 数据卷: /opt/atlas/data/postgres
```

### 3.2 部署命令速查

**后端重启**：
```bash
systemctl restart atlas-api
systemctl status atlas-api
journalctl -u atlas-api -f   # 查看日志
```

**前端更新**：
```bash
cd /root/work/atlas/frontend
npm run build
cp -r dist /opt/atlas/web/
```

**数据库迁移**：
```bash
cd /root/work/atlas/backend
source .venv/bin/activate
alembic upgrade head
```

**权限点补种**（新增权限点时）：
```bash
cd /root/work/atlas/backend
source .venv/bin/activate
python scripts/seed_permissions.py   # 幂等执行，已有不会重复插入
```

**种子数据初始化**（仅开发环境）：
```bash
cd /root/work/atlas/backend
source .venv/bin/activate
python scripts/seed.py   # 初始化 admin 用户、组织、对象类型、关系类型等
```

**数据库连接信息**：
- 开发库：`postgresql+psycopg://atlas:atlas@localhost:55433/atlas_dev`
- 测试库：`postgresql+psycopg://atlas:atlas@localhost:5432/atlas_test`（CI 使用）
- 生产库：`postgresql+psycopg://atlas:atlas@localhost:55433/atlas_prod`（部署时配置）

---

## 4. 已知遗留与后续建议

### 4.1 功能遗留

**Phase 6: Agent 采集（未开始）**
- 状态：设计文档已完成，代码未实现
- 范围：Go Agent 框架 + Redfish/IPMI/SNMP/nvidia-smi 采集器 + 采集调度
- 优先级：P4（非 MVP 必须，可作为后续增强）
- 建议：若需要自动采集能力，优先实现 Redfish 采集器（覆盖大部分服务器硬件信息）

**知识 AI LLM 配置 UI**
- 状态：后端 API 已完成，前端未提供配置页面
- 当前：LLM 配置需通过 API 或数据库直接插入
- 建议：新增 `/knowledge/llm-configs` 前端页面（管理员权限），支持 CRUD 操作

**对象级权限细粒度控制**
- 状态：当前仅支持组织级隔离（organization_id），不支持单个对象的权限控制
- 建议：若需要对象级权限（如"用户 A 只能查看对象 X"），需扩展权限模型（增加 object-level ACL 表）

**operator/viewer 角色真实数据验证**
- 状态：已定义 operator/viewer 角色（backend/scripts/seed_permissions.py），但未充分验证其权限边界
- 建议：创建 operator/viewer 测试账号，验证以下场景：
  - operator 能否查看 Dashboard、创建工单，但不能删除对象
  - viewer 能否只读查看所有数据，但无法修改任何内容

**工作流引擎支持更多流程类型**
- 状态：当前仅接入采购审批流程（purchase_approval），工作流引擎本身通用
- 建议：接入更多流程类型（如工单审批、资产部署审批、退役审批），复用工作流引擎

**数据质量规则自动触发**
- 状态：当前质量检查需手动触发（`POST /api/v1/quality/rules/{id}/check`）
- 建议：增加定时任务（Celery 或 APScheduler），定期自动执行质量检查

### 4.2 技术债

**前端状态管理**
- 状态：部分页面未使用 Pinia store，直接在组件内管理状态
- 建议：对于跨组件共享的状态（如当前用户信息、未读通知数），统一使用 Pinia store

**后端 Service 层不完整**
- 状态：部分 API 直接在 router 层写业务逻辑，未抽取到 service 层
- 建议：重构复杂业务逻辑（如资产生命周期、工单流转），统一抽取到 `backend/app/services/` 目录

**日志与监控**
- 状态：后端已有日志（journalctl -u atlas-api），但缺乏结构化日志与监控告警
- 建议：接入 ELK/Loki 或 Prometheus + Grafana，监控 API 响应时间、数据库连接池、错误率

**前端错误边界**
- 状态：部分 API 调用未处理错误场景（如网络超时、401 未登录）
- 建议：增加全局 axios 拦截器，统一处理 401（跳转登录）、403（权限不足提示）、500（友好错误提示）

### 4.3 性能优化建议

**对象列表分页**
- 状态：当前 `/api/v1/objects` 返回全量数据（若对象数 > 1000 会慢）
- 建议：增加分页参数（limit/offset 或 page/page_size），前端使用虚拟滚动或分页器

**Dashboard 统计缓存**
- 状态：Dashboard 每次访问都实时查询数据库聚合（数据量大时慢）
- 建议：增加 Redis 缓存（TTL 5 分钟），或预计算统计数据（定时任务）

**对象历史记录压缩**
- 状态：`object_history` 表记录 before/after 完整 JSON（数据量大时占用空间）
- 建议：仅记录变更字段（diff），或定期归档历史数据（如 1 年前数据迁移到归档库）

---

## 5. 给下一位开发者的指引

### 5.1 必读文档顺序

1. **AGENTS.md**（根目录）：理解开发规范与禁止事项
2. **docs/PROGRESS.md**（当前文件）：当前进度、模块总览、已知遗留
3. **docs/16-Atlas开发任务拆解与Codex执行计划.md**：Phase 0-6 详细任务与验收标准
4. **docs/11-Atlas-MVP版本开发规划.md**：MVP 总体目标与交付清单
5. **根据任务类型阅读对应设计文档**（docs/02-12）

### 5.2 数据库连接速查

**开发库**（本地开发 + 生产环境）：
```bash
psql postgresql://atlas:atlas@localhost:55433/atlas_dev
```

**测试库**（pytest 自动使用）：
```bash
psql postgresql://atlas:atlas@localhost:5432/atlas_test
```

**数据库迁移流程**：
1. 修改模型：`backend/app/models/*.py`
2. 生成迁移：`cd backend && alembic revision --autogenerate -m "描述"`
3. 检查迁移脚本：`backend/alembic/versions/xxx_描述.py`
4. 执行迁移：`alembic upgrade head`（开发库和生产库都需执行）

### 5.3 种子数据说明

**seed_permissions.py**（权限点补种，幂等执行）：
- 作用：初始化 18 个权限点 + 3 个角色（admin/operator/viewer）+ 角色权限关联
- 时机：每次新增权限点后，需在开发库和生产库执行
- 命令：`cd backend && python scripts/seed_permissions.py`

**seed.py**（种子数据初始化，仅开发环境）：
- 作用：初始化 admin 用户（admin/atlas123456）+ 默认组织 + 对象类型 + 关系类型
- 时机：仅在开发环境首次初始化时执行，生产环境不执行（避免覆盖真实数据）
- 命令：`cd backend && python scripts/seed.py`

### 5.4 部署命令速查

**后端重启**：
```bash
systemctl restart atlas-api
journalctl -u atlas-api -f   # 查看日志
```

**前端更新**：
```bash
cd /root/work/atlas/frontend
npm run build
cp -r dist /opt/atlas/web/
```

**数据库迁移**：
```bash
cd /root/work/atlas/backend
source .venv/bin/activate
alembic upgrade head
```

**权限点补种**：
```bash
cd /root/work/atlas/backend
source .venv/bin/activate
python scripts/seed_permissions.py
```

### 5.5 开发约定

**禁止事项**（AGENTS.md 明确规定）：
- ❌ 创建 `gpu_table`、`server_table` 等专用设备表（所有设备必须通过 `objects` 表建模）
- ❌ 未经确认擅自拆分微服务（MVP 阶段采用模块化单体）
- ❌ 未经确认更换数据库（必须使用 PostgreSQL）
- ❌ 未经确认修改核心模型（Object/Relationship/History 的表结构与字段定义）

**推荐实现顺序**：
1. 数据库迁移（Alembic migration）
2. 数据模型（SQLAlchemy models）
3. Schema 定义（Pydantic schemas）
4. 业务逻辑（Service 层）
5. API 路由（FastAPI routers）
6. 前端页面（Vue 3 组件）
7. 单元测试与集成测试
8. 文档更新

**Git Commit 规范**：
- `feat: 新增知识 AI 问答`
- `fix: 修复对象关系查询问题`
- `refactor: 优化资产生命周期逻辑`
- `docs: 更新 PROGRESS.md`

---

## 6. 附录

### 6.1 关键 Commit 历史

| Commit | 功能 | 日期 |
| --- | --- | --- |
| 7d68bc7 | Phase 0 工程初始化 | 2026-09-03 |
| dc84a6a | Phase 1 Infrastructure Core + Object Explorer | 2026-09-03 |
| 392ee4c | Phase 2 数据接入层 | 2026-09-03 |
| 0b546d3 | Phase 3 Asset Management | 2026-09-03 |
| 327759f | Phase 4 Operations Management | 2026-09-03 |
| f4acaab | Phase 5 Dashboard + Knowledge | 2026-09-03 |
| 726fc0a | CI/CD + 测试库隔离 | 2026-09-04 |
| ed5101f | 登录认证 + JWT | 2026-09-04 |
| 5637943 | RBAC 权限体系 | 2026-09-04 |
| d8c668c | 多组织隔离 | 2026-09-04 |
| 365158a | 工作流引擎 + 采购审批 | 2026-09-04 |
| ead19aa | 站内通知 | 2026-09-04 |
| 425a968 | 数据质量中心 | 2026-09-04 |
| 415fbef | 知识 AI 问答 | 2026-09-04 |
| bf83f6d | 前端整合（通知/审批/质量/AI/角色化） | 2026-09-04 |

### 6.2 联系方式

如有疑问，请参考：
- **设计文档**：`docs/` 目录（18 篇）
- **开发规范**：`AGENTS.md`
- **开发计划**：`docs/16-Atlas开发任务拆解与Codex执行计划.md`
- **Git 历史**：`git log --oneline --all`

---

**文档结束**
