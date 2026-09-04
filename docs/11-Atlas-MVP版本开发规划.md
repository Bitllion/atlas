# Atlas MVP 版本开发规划

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | ✅ MVP 已交付（Phase 0-5, 2026-09-04） |

**交付总览**：

- **核心阶段**：Phase 0-5 已完成并合并至 main 分支（Phase 6 Agent 采集为非 MVP 范围）
- **提交记录**：见 `git log --oneline` 从 7d68bc7（Phase 0）到 bf83f6d（前端整合）
- **测试基线**：pytest 65 passed（CI 自动执行，测试库 atlas_test 隔离）
- **生产部署**：systemd atlas-api + nginx 80 + PostgreSQL 容器 atlas-dev-pg:55433
- **演示账号**：admin / atlas123456（管理员权限，可访问全部功能）

## 1. 总体目标

> 建立 AI 基础设施资源数字化管理平台，实现设备对象建模、资产管理以及基础运营能力。

一期重点是模型正确、数据可管理、业务可运行；暂不重点实现自动化、实时监控、AI 助手和复杂流程。

## 2. 优先级与 Phase 映射

> **阶段定义唯一权威：docs/16-Atlas开发任务拆解与Codex执行计划.md**
> 
> 本文档优先级与 Phase 的对应关系：

| 优先级 | Phase | 交付内容 | 验收标准 |
| --- | --- | --- | --- |
| P0 | Phase 0 | 工程初始化 | 健康检查接口、数据库连接、前后端可启动 |
| P0 | Phase 1 | Infrastructure Core + Object Explorer | 能创建 GB300 Rack/Compute Tray/GPU/NIC 并查看关系 |
| P1 | Phase 2 | 数据接入层 | 能批量导入设备清单（Excel/CSV） |
| P1 | Phase 3 | Asset Management + Asset 页面 | 完整采购到部署流程可操作 |
| P2 | Phase 4 | Operations Management + Operations 页面 | 完整工单生命周期可操作 |
| P2/P3 | Phase 5 | Dashboard + Knowledge | Dashboard 展示设备/资产/工单统计 |
| P4 | Phase 6 | Agent 采集（非 MVP 必须） | 自动采集服务器/GPU 信息 |

### 2.1 优先级定义

```text
P0 Infrastructure Core（基础设施核心）
P1 Asset Management（资产管理）
P2 Basic Operations（基础运维）
P3 Knowledge（知识管理）
P4 Automation（自动化采集）
```

## 3. 分阶段范围

### Phase 0: 工程初始化（P0）

- 仓库结构、CI/CD、Docker Compose
- 前后端脚手架（Python/FastAPI + Vue 3/TypeScript）
- 数据库连接与 Alembic 迁移框架
- 健康检查接口 `/health`

### Phase 1: Infrastructure Core + Object Explorer（P0）

- **后端**：Object、ObjectType、ObjectSpec、Relationship、RelationshipType、History 模型与 CRUD API
- **数据库**：Core 域表 + 基础权限表（users/roles/permissions/organizations）+ idempotency_keys + audit_logs
- **前端**：Object Explorer 页面（列表、详情、关系图、历史记录）
- **验收**：能创建 GB300 Rack、Compute Tray、GPU、BF3 NIC，建立 contains/installed_in/connected_to 关系，查看对象详情与历史

支持对象类型：Data Center、Room、Rack、Server、GPU、NIC、Storage、CDU、Power Shelf。

### Phase 2: 数据接入层（P1，Asset 依赖）

- **后端**：Excel/CSV/JSON 导入 API，支持 dry_run 模式与错误反馈
- **功能**：批量创建对象与关系、导入历史记录、重复检测
- **验收**：能通过 Excel 批量导入 100 台服务器清单并预览错误

### Phase 3: Asset Management（P1）

- **后端**：采购申请、验收、库存、部署、资产台账 API
- **数据库**：assets、purchases、inventory_locations、deployments 表
- **前端**：Asset 管理页面（采购流程、库存视图、资产台账）
- **验收**：完整走完采购申请 → 批准 → 到货 → 入库 → 部署流程，查看资产生命周期

### Phase 4: Operations Management（P2）

- **后端**：工单、故障、维修、部件更换 API
- **数据库**：work_orders、faults、repairs、component_replacements 表
- **前端**：Operations 管理页面（工单流转、故障处理、维修记录）
- **验收**：创建故障工单 → 分配工程师 → 更换部件 → 关闭工单，查看完整工单历史

### Phase 5: Dashboard 与 Knowledge（P2/P3）

- **Dashboard**：汇总 Core/Asset/Operations 数据的综合视图（设备统计、资产状态、工单趋势）
- **Knowledge**：文档上传、分类、对象关联
- **搜索**：全局对象搜索（按名称、SN、型号、状态）
- **验收**：Dashboard 展示设备数量、资产分布、工单统计；能上传 SOP 并关联到设备

### Phase 6: Agent 采集（P4，非 MVP 必须）

- **Agent**：Go Agent 框架、Redfish、IPMI、SNMP、nvidia-smi 采集器
- **后端**：采集调度、数据治理（agents/collection_jobs/collection_failures 表）
- **验收**：Agent 自动采集服务器硬件信息（CPU/内存/磁盘/网卡）与 GPU 状态（温度/利用率/功耗）

预留接口：PXE、Firmware 升级、自动修复（不实现）。

## 4. MVP 验收标准

### 4.1 必达目标（✅ 已实现）

MVP 必须能够：

1. **对象建模**：创建 GB300 Rack、Compute Tray、GPU、BF3 NIC、CDU、Power Shelf，建立 contains/installed_in/connected_to/powered_by 关系 ✅
2. **资产管理**：完整走完采购申请 → 到货验收 → 入库 → 部署流程，查看资产生命周期 ✅
3. **运维管理**：创建故障工单 → 分配工程师 → 更换部件 → 关闭工单，查看维修记录 ✅
4. **数据导入**：批量导入设备清单（Excel/CSV），预览错误并修正 ✅
5. **Dashboard**：查看设备总数、资产状态分布、工单趋势 ✅

### 4.2 实际交付清单（Phase 0-5）

**Phase 0: 工程初始化** ✅
- 前后端脚手架（Python 3.12 + FastAPI + Vue 3 + TypeScript）
- Docker Compose 环境
- Alembic 数据库迁移框架
- 健康检查接口 `/health`

**Phase 1: Infrastructure Core + Object Explorer** ✅
- 核心对象模型（objects/object_types/relationships/object_specs/object_history）
- Object CRUD API（13 个端点）
- Object Explorer 前端（列表/详情/关系图/历史时间线）
- 基础权限表（users/roles/permissions/organizations）

**Phase 2: 数据接入层** ✅
- Excel/CSV 批量导入 API（preview + execute）
- 导入任务记录与错误反馈
- 导入前端页面（上传/预览/历史）

**Phase 3: Asset Management** ✅
- 资产全生命周期（采购/验收/入库/部署/调拨/退役）
- 资产台账页面
- 采购申请与库存管理

**Phase 4: Operations Management** ✅
- 工单系统（work_orders/faults/repairs/component_replacements）
- 工单流转与状态机
- 工单详情页与时间线

**Phase 5: Dashboard 与 Knowledge** ✅
- Dashboard 概览（设备/资产/工单统计，支持按组织过滤）
- 知识库（文章/附件/对象关联）
- 知识 AI 问答（可配置 LLM，支持 RAG 检索）
- 全局搜索

**MVP 增强功能** ✅（Phase 0-5 之后）
- CI/CD：GitHub Actions 流水线 + pytest 测试库隔离
- 登录认证：JWT + 双通道兼容（dev/prod）
- RBAC 权限体系：18 个权限点 + 资源范围隔离
- 多组织隔离：读写隔离 + Dashboard 组织统计
- 通用工作流引擎：采购审批接入（A1/A2 节点）
- 站内通知：工单/审批任务通知 + 前端铃铛
- 数据质量中心：质量规则 + 问题记录 + 质量报告
- 前端角色化：基于权限点的菜单/按钮显隐

### 4.3 测试基线

- **单元测试 + 集成测试**：65 passed（backend/tests/）
- **测试覆盖模块**：
  - Core: objects/relationships/search
  - Asset: assets/purchases/deployments
  - Operations: work_orders/faults/repairs
  - Dashboard: statistics/charts
  - Workflow: engine/tasks/instances
  - Notifications: push/read/unread-count
  - Quality: rules/issues/reports
  - Scope: organization read/write isolation
- **CI 自动化**：每次 push 到 main 或 PR 时自动运行 pytest（atlas_test 数据库隔离）
- **测试数据库**：`atlas_test`（与开发库 `atlas_dev` 隔离，避免污染）

### 4.2 页面清单

| 页面 | Phase | 说明 |
| --- | --- | --- |
| Object Explorer | Phase 1 | 对象列表、详情、关系图、历史记录 |
| Asset Management | Phase 3 | 采购流程、库存视图、资产台账 |
| Operations | Phase 4 | 工单流转、故障处理、维修记录 |
| Dashboard | Phase 5 | 设备统计、资产分布、工单趋势 |
| Knowledge | Phase 5 | 文档上传、分类、对象关联 |

## 5. 开发路线

```text
Phase 0 工程初始化
    ↓
Phase 1 Infrastructure Core + Object Explorer
    ↓
Phase 2 数据接入层（为 Asset 准备）
    ↓
Phase 3 Asset Management + Asset 页面
    ↓
Phase 4 Operations Management + Operations 页面
    ↓
Phase 5 Dashboard + Knowledge
    ↓
Phase 6 Agent 采集（可选）
```

每个 Phase 必须包含：后端 API + 前端页面 + 数据库迁移 + 测试 + 文档更新，确保端到端可验收。
