# Atlas MVP 版本开发规划

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | 开发规划文档 |

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

### 4.1 必达目标

MVP 必须能够：

1. **对象建模**：创建 GB300 Rack、Compute Tray、GPU、BF3 NIC、CDU、Power Shelf，建立 contains/installed_in/connected_to/powered_by 关系
2. **资产管理**：完整走完采购申请 → 到货验收 → 入库 → 部署流程，查看资产生命周期
3. **运维管理**：创建故障工单 → 分配工程师 → 更换部件 → 关闭工单，查看维修记录
4. **数据导入**：批量导入设备清单（Excel/CSV），预览错误并修正
5. **Dashboard**：查看设备总数、资产状态分布、工单趋势

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
