# Atlas Platform

## AI Infrastructure Intelligent Operations Management Platform

Atlas 是一个面向 AI 数据中心、高性能计算（HPC）以及企业级基础设施环境的智能运营管理平台。

> 构建 AI 基础设施数字化底座，实现从资源建模、资产管理、运维运营到智能化演进的一体化管理。

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

## 整体架构

```text
User → Atlas Web → Backend API
                    ├── Object Core
                    ├── Asset
                    ├── Operations
                    ├── Knowledge
                    ├── Workflow
                    └── Permission
                          ↓
                     PostgreSQL
                          ↓
              Agent / Import / External Source
```

Atlas 采用模块化单体与独立 Agent 架构，MVP 阶段不提前微服务化。

## 技术架构

- Backend：Python、FastAPI、SQLAlchemy、PostgreSQL
- Frontend：Vue 3、TypeScript、Vite、Element Plus
- Agent：Go，负责 Redfish、IPMI、SNMP 和 Linux Hardware Discovery
- Deployment：Docker Compose

## 项目结构

```text
atlas-platform/
├── AGENTS.md
├── README.md
├── docs/
├── backend/
├── frontend/
├── agent/
├── database/
├── docker/
└── scripts/
```

## 开发环境

推荐使用 PVE Ubuntu VM、SSH、Codex CLI 和 Docker。开发前必须阅读根目录 `AGENTS.md` 以及 `docs/`。

```bash
docker compose up --build -d
docker compose exec backend alembic upgrade head
```

服务地址：

- 前端欢迎页：http://localhost:3000
- 后端健康检查：http://localhost:8000/health
- Swagger UI：http://localhost:8000/docs
- PostgreSQL：`localhost:55433`（容器内仍为 `5432`，避免占用宿主机已有端口）

查看服务状态和日志：

```bash
docker compose ps
docker compose logs -f
docker compose down
```

本地启动后端（Python 3.12，pip 使用清华镜像）：

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

本地启动前端（npm 使用 npmmirror 镜像）：

```bash
cd frontend
npm config set registry https://registry.npmmirror.com
npm install
npm run dev
```

本地运行 Alembic 前，请确保 PostgreSQL 已在 `localhost:55433` 启动：

```bash
cd backend
alembic upgrade head
```

## 文档体系

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
```

## MVP 路线

```text
Phase 1 基础平台：Object、Relationship、History
Phase 2 资产管理：采购、验收、入库、部署
Phase 3 运维管理：工单、故障、维修
Phase 4 数据能力：Excel 导入、数据治理、来源管理
Phase 5 智能化：Agent、AI Assistant、RAG、自动化运营
```

## 目标

Atlas 不是简单资产管理系统，也不是传统 CMDB，而是 AI 时代基础设施的数字化运营平台。
