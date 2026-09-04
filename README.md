# Atlas Platform

## AI Infrastructure Intelligent Operations Management Platform

Atlas 是一个面向 AI 数据中心、高性能计算（HPC）以及企业级基础设施环境的智能运营管理平台。

> 构建 AI 基础设施数字化底座，实现从资源建模、资产管理、运维运营到智能化演进的一体化管理。

## 当前状态

**✅ MVP Phase 0-5 已交付（2026-09-04）**

### 功能全景

| 模块 | 功能 | 状态 |
| --- | --- | --- |
| **Infrastructure Core** | 对象建模、关系管理、规格管理、历史追踪 | ✅ 已完成 |
| **Object Explorer** | 对象列表、详情、关系图、历史时间线 | ✅ 已完成 |
| **数据接入** | Excel/CSV 批量导入、预览、错误反馈 | ✅ 已完成 |
| **资产管理** | 采购申请、验收、入库、部署、调拨、退役 | ✅ 已完成 |
| **运维管理** | 工单、故障、维修、部件更换、状态流转 | ✅ 已完成 |
| **Dashboard** | 设备统计、资产分布、工单趋势、组织过滤 | ✅ 已完成 |
| **知识库** | 文章管理、附件上传、对象关联 | ✅ 已完成 |
| **知识 AI** | LLM 问答（可配置）、RAG 检索 | ✅ 已完成 |
| **全局搜索** | 按名称/SN/型号/标签搜索对象 | ✅ 已完成 |
| **登录认证** | JWT + 双通道（dev/prod） | ✅ 已完成 |
| **权限体系** | RBAC 18 权限点 + 资源范围隔离 | ✅ 已完成 |
| **多组织** | 读写隔离 + Dashboard 组织统计 | ✅ 已完成 |
| **工作流引擎** | 通用工作流 + 采购审批接入 | ✅ 已完成 |
| **站内通知** | 工单/审批任务通知 + 前端铃铛 | ✅ 已完成 |
| **数据质量** | 质量规则 + 问题记录 + 质量报告 | ✅ 已完成 |
| **前端角色化** | 基于权限点的菜单/按钮显隐 | ✅ 已完成 |
| **CI/CD** | GitHub Actions + pytest 测试库隔离 | ✅ 已完成 |
| **Agent 采集** | 自动采集服务器/GPU 信息 | ❌ 未开始（非 MVP）|

### 测试与质量

- **测试用例**：65 passed（单元测试 + 集成测试）
- **测试覆盖**：Core / Asset / Operations / Dashboard / Workflow / Notifications / Quality / Scope
- **CI 自动化**：每次 push 到 main 或 PR 时自动运行 pytest
- **测试库隔离**：`atlas_test` 与开发库 `atlas_dev` 隔离

### 演示账号

- **用户名**：`admin`
- **密码**：`atlas123456`
- **权限**：管理员（可访问全部功能）

## 设计理念

- Object First：所有基础设施实体统一抽象为 Infrastructure Object。
- Relationship Driven：通过关系表达设备连接和基础设施拓扑。
- Lifecycle Management：覆盖采购、验收、入库、部署、运行、维护和退役。
- Data Governance：支持自动采集、手工录入、Excel 导入、文档、客户反馈和厂商资料，并记录来源、时间、可信度和历史变化。

## 核心能力

- Infrastructure Object Management
- Relationship Management
- Asset Management
- Operations Management
- Knowledge Management
- Workflow Engine
- Multi Organization & Permission

### 架构模式

```text
User → Atlas Web (Vue 3) → Backend API (FastAPI)
                              ├── Infrastructure Core (objects/relationships)
                              ├── Asset Management (purchases/assets/deployments)
                              ├── Operations Management (work_orders/faults/repairs)
                              ├── Knowledge Management (articles/attachments)
                              ├── Workflow Engine (instances/tasks)
                              ├── Notification System (notifications)
                              ├── Data Quality (rules/issues/reports)
                              └── Permission & Organization (RBAC + multi-org isolation)
                                    ↓
                              PostgreSQL 17 (Container: atlas-dev-pg:55433)
                                    ↓
                        Agent / Import / External Source (未来扩展)
```

Atlas 采用**模块化单体架构** + 独立 Agent 采集（预留），MVP 阶段不微服务化。

## 技术架构

### 技术栈

- **后端**：Python 3.12、FastAPI、SQLAlchemy、PostgreSQL 17、Alembic
- **前端**：Vue 3、TypeScript、Vite、Element Plus、Vue Router、Axios
- **测试**：pytest、GitHub Actions
- **部署**：systemd（后端）+ nginx（前端）+ Docker（PostgreSQL）
- **Agent**：Go（预留，未实现）

### 架构模式

## 项目结构

```text
atlas/
├── README.md                      # 项目总览（当前文件）
├── AGENTS.md                      # AI Agent 开发规范（必读）
├── docs/                          # 设计文档（18 篇）
│   ├── 00-产品定义.md
│   ├── 01-Atlas业务架构设计.md
│   ├── 02-基础设施对象模型.md
│   ├── 11-Atlas-MVP版本开发规划.md
│   ├── 16-Atlas开发任务拆解与Codex执行计划.md
│   ├── 18-Atlas MVP数据库初始化与第一批开发任务.md
│   └── PROGRESS.md                # 开发进度与交接文档
├── backend/                       # 后端（Python + FastAPI）
│   ├── app/
│   │   ├── main.py               # FastAPI 应用入口
│   │   ├── models/               # SQLAlchemy 数据模型
│   │   ├── schemas/              # Pydantic 请求/响应模型
│   │   ├── api/v1/               # API 路由
│   │   ├── services/             # 业务逻辑层
│   │   ├── core/                 # 核心配置（auth/deps/security）
│   │   └── utils/                # 工具函数
│   ├── alembic/                  # 数据库迁移
│   ├── scripts/                  # 初始化脚本（seed/seed_permissions）
│   ├── tests/                    # pytest 测试（20 个测试文件，65 passed）
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/                      # 前端（Vue 3 + TypeScript）
│   ├── src/
│   │   ├── views/                # 页面组件（13+ 页面）
│   │   ├── components/           # 通用组件
│   │   ├── router/               # Vue Router 路由
│   │   ├── api/                  # API 封装（axios）
│   │   ├── stores/               # Pinia 状态管理
│   │   └── utils/                # 工具函数
│   ├── package.json
│   └── vite.config.ts
├── .github/workflows/ci.yml       # GitHub Actions CI 流水线
└── docker-compose.yml             # Docker Compose 配置（PostgreSQL）
```

**关键目录说明**：
- `docs/`：设计文档，开发前必读（优先级：AGENTS.md → PROGRESS.md → 16 → 11 → 其他）
- `backend/app/models/`：数据库模型（27+ 表），遵循 Object First 原则
- `backend/tests/`：测试用例，覆盖 Core/Asset/Ops/Dashboard/Workflow/Notifications/Quality
- `frontend/src/views/`：页面组件，按模块组织（Objects/Assets/WorkOrders/Dashboard/Knowledge/Approvals/DataQuality）

## 快速启动

### 本地开发环境

**环境要求**：
- Python 3.12
- Node.js 22
- PostgreSQL 17（或 Docker）

**1. 启动数据库（Docker）**

```bash
cd /root/work/atlas
docker compose up -d postgres
```

PostgreSQL 地址：`localhost:55433`（容器内为 5432，避免占用宿主机端口）

**2. 初始化数据库**

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
alembic upgrade head
python scripts/seed_permissions.py   # 初始化权限点
python scripts/seed.py              # 初始化种子数据（admin 用户、组织、对象类型等）
```

**3. 启动后端**

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- 健康检查：http://localhost:8000/health
- Swagger UI：http://localhost:8000/docs

**4. 启动前端**

```bash
cd frontend
npm config set registry https://registry.npmmirror.com
npm install
npm run dev
```

- 前端地址：http://localhost:3000
- 登录账号：admin / atlas123456

### 生产部署

**架构**：
- **后端**：systemd 服务 `atlas-api`（gunicorn + uvicorn workers）
- **前端**：nginx 静态文件（/opt/atlas/web/dist）
- **数据库**：Docker 容器 `atlas-dev-pg`（端口 55433）

**部署命令**：

```bash
# 后端重启
systemctl restart atlas-api
journalctl -u atlas-api -f   # 查看日志

# 前端更新
cd /root/work/atlas/frontend
npm run build
cp -r dist /opt/atlas/web/

# 数据库迁移
cd /root/work/atlas/backend
source .venv/bin/activate
alembic upgrade head

# 权限点补种（新增权限点时）
python scripts/seed_permissions.py
```

**服务地址**：
- 前端：http://<server-ip>:80
- 后端 API：http://<server-ip>:8000
- 数据库：<server-ip>:55433（需内网访问）

## 文档体系

开发前必读文档优先级（按顺序）：

1. **AGENTS.md**：理解 AI Agent 开发规范与禁止事项
2. **docs/PROGRESS.md**：当前进度、模块总览、已知遗留
3. **docs/16-Atlas开发任务拆解与Codex执行计划.md**：Phase 0-6 详细任务与验收标准
4. **docs/11-Atlas-MVP版本开发规划.md**：MVP 总体目标与交付清单
5. **根据任务类型阅读对应设计文档**：
   - 对象模型：`docs/02-基础设施对象模型.md`
   - 资产管理：`docs/04-Atlas资产管理业务设计.md`
   - 运维管理：`docs/05-Atlas运维管理业务设计.md`
   - 工作流：`docs/07-Atlas工作流与状态机设计.md`
   - 权限：`docs/08-Atlas权限与多组织模型设计.md`
   - 数据库：`docs/12-Atlas数据库模型设计.md`
   - API：`docs/13-Atlas-API设计规范.md`

完整文档列表：

```text
00 产品定义
01 业务架构
02 Object 模型
03 Relationship 模型
04 Asset 管理
05 Operations 管理
06 Knowledge 管理
07 Workflow 设计
08 权限与组织模型
09 数据治理
10 系统架构
11 MVP 规划
12 数据库设计
13 API 设计
14 前端设计
15 工程规范
16 开发计划
17 AGENTS.md 设计说明
18 MVP 数据库初始化与第一批开发任务
PROGRESS 开发进度与交接
```

## MVP 路线（已完成 Phase 0-5）

```text
✅ Phase 0 工程初始化（commit 7d68bc7）
    ↓
✅ Phase 1 Infrastructure Core + Object Explorer（commit dc84a6a）
    ↓
✅ Phase 2 数据接入层（commit 392ee4c）
    ↓
✅ Phase 3 Asset Management（commit 0b546d3）
    ↓
✅ Phase 4 Operations Management（commit 327759f）
    ↓
✅ Phase 5 Dashboard + Knowledge（commit f4acaab）
    ↓
✅ MVP 增强（commit bf83f6d）：
    - CI/CD + 测试库隔离（commit 726fc0a）
    - 登录认证 + JWT（commit ed5101f）
    - RBAC 权限体系（commit 5637943）
    - 多组织隔离（commit d8c668c）
    - 工作流引擎 + 采购审批（commit 365158a）
    - 站内通知（commit ead19aa）
    - 数据质量中心（commit 425a968）
    - 知识 AI 问答（commit 415fbef）
    - 前端整合（commit bf83f6d）
    ↓
❌ Phase 6 Agent 采集（未开始，非 MVP 范围）
```

每个 Phase 包含：后端 API + 前端页面 + 数据库迁移 + 测试 + 文档更新。

## 目标

Atlas 不是简单资产管理系统，也不是传统 CMDB，而是 AI 时代基础设施的数字化运营平台。
