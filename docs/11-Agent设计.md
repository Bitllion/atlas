# Agent 设计

## 1. 定位

Agent 用于硬件采集、长时间运行任务和后续自动化能力，不替代 Atlas Core，也不直接承载资产和工单主数据。

## 2. 支持方式

- Redfish
- IPMI
- SNMP
- `nvidia-smi`
- `lspci`
- `ethtool`

## 3. 设计要求

- Go 实现，支持独立部署。
- 任务可重试、可恢复、可观测。
- 采集结果必须包含对象标识、来源、时间、状态和错误信息。
- 采集失败不得删除或覆盖可信的历史数据。
- 客户环境无授权时不得执行主动操作。

## 4. 数据流

```text
Agent → Data Source Service → Object/Specification Service → History
```

自动化执行必须额外经过 Permission、Management Scope 和 Customer Authorization 判断。
