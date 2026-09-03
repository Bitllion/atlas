# Atlas 代码工程结构规范

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | 工程规范文档 |

## 1. 单仓库结构

```text
atlas-platform/
├── AGENTS.md
├── README.md
├── backend/
├── frontend/
├── agent/
├── database/
├── docker/
├── docs/
├── scripts/
└── tests/
```

## 2. Backend

```text
backend/
├── app/{main.py,config,database,models,schemas,api,services,core,utils}
├── migrations/
├── tests/
├── requirements.txt
└── Dockerfile
```

Core 包含 Object、Relationship、Specification、History 和 DataSource，Core 不依赖业务模块。API 只负责校验并调用 Service，业务逻辑遵循 `API → Service → Repository → Database`。

## 3. Frontend、Agent 与配置

```text
frontend/src/{api,views,components,stores,router,utils}
agent/{collector,redfish,ipmi,snmp,linux,main.go}
database/{migrations,init.sql,seed}
docker/{docker-compose.yml,backend,frontend,postgres}
```

Agent 只负责采集，不负责资产逻辑、Workflow 或 Permission。密码、Token 和地址不得写入代码，使用 `.env` 或安全配置。

## 4. Git 与演进

可使用 main、develop 和 feature/*；Commit 使用 feat、fix、docs、refactor 前缀。MVP 顺序为工程初始化、Core、Asset、Operations、Search / Import / Dashboard；禁止提前微服务化。
