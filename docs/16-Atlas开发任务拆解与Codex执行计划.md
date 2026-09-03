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

## 2. 阶段任务

- Phase 0：创建工程目录，完成 Python、FastAPI、PostgreSQL、Vue 3、TypeScript、Router 和配置管理；验收 `/health` 返回 `{"status":"ok"}`。
- Phase 1：实现 Object、ObjectType、ObjectSpec、Relationship、History；创建 GB300 Rack、Compute Tray、GPU 并展示关系。
- Phase 2：实现采购、验收、库存和部署。
- Phase 3：实现 Work Order、Fault、Repair。
- Phase 4：实现 Dashboard、Object Detail、Asset、Operations 和 Knowledge 页面。
- Phase 5：实现 Excel、CSV、JSON 导入。
- Phase 6：MVP 后实现 Go Agent、Redfish、IPMI、SNMP、lspci 和 nvidia-smi。

## 3. Codex 规则

每次任务先阅读 `AGENTS.md` 和相关 docs，确认数据模型、API 和页面边界后再编码。不得创建 `gpu_table`、`server_table`，不得未经确认拆微服务、更换数据库或修改核心模型，也不得超范围实现 AI Agent、自动修复和 PXE。

## 4. 输出与验收

完成每项任务必须输出修改文件、数据库变化、API 变化和测试结果。每个阶段必须满足代码可运行、数据库结构正确、API 可调用、前端可操作、文档同步更新，并提交 Git commit。

## 5. MVP 与后续

MVP 能管理 Data Center、Rack、Server、GPU、NIC、CDU，完成 Object、Relationship、History、采购、入库、部署、工单、故障和维修。V2 为 Agent，V3 为 Knowledge AI / RAG，V4 为 Automation / PXE / Firmware / Validation。
