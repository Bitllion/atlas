# Atlas 系统架构设计

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | 系统架构设计文档 |

## 1. 架构原则

Atlas 采用模块化单体（Modular Monolith）与独立采集 Agent。MVP 阶段不提前拆分大量微服务、Kubernetes 或复杂治理组件。

## 2. 总体架构

```text
User → Web Frontend → API Layer → Atlas Backend
                                      ├── Object Core
                                      ├── Asset
                                      ├── Operations
                                      ├── Knowledge
                                      ├── Workflow
                                      └── Permission
                                            ↓
                                       PostgreSQL

Agent / Import / External Source → Data Collection Layer
```

## 3. 技术选型

- Backend：Python、FastAPI、SQLAlchemy、PostgreSQL
- Frontend：Vue 3、TypeScript
- Agent：Go
- Deployment：Docker Compose

Python 适合快速迭代对象、关系和工作流模型，也便于集成 RAG、LLM 和数据分析；一期主要负载是 CRUD、查询和数据管理。

## 4. 模块边界

Core 包含 Object、Relationship、Specification、History 和 Data Source，业务模块依赖 Core，Core 不依赖业务模块。Asset 负责采购、库存、部署和生命周期；Operations 负责工单、故障、巡检和维修；Knowledge 负责文档、SOP 和案例；Workflow 负责流程，不存业务主数据。

## 5. Agent、导入与部署

Agent 只负责获取基础设施数据，不负责业务逻辑。支持 Redfish、IPMI、SNMP、dmidecode、lspci、nvidia-smi 和 ethtool；Excel、CSV、JSON 用于初始资产导入和客户数据同步。

支持单机、企业和无公网环境，Docker Compose 优先。未来模块成熟后再拆分服务。
