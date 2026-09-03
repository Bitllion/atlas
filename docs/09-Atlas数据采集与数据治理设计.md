# Atlas 数据采集与数据治理设计

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | 数据架构设计文档 |

## 1. 目标

将不同来源、不同可信度和不同时间的数据融合为可运营的基础设施模型。Atlas 不把实时采集成功作为设备存在的前提。

## 2. 数据来源

- Discovery：IPMI、Redfish、SNMP、Agent
- Manual：工程师人工录入
- Import：Excel、CSV、JSON
- Document：PDF、Datasheet、验收报告
- Customer Report：客户反馈
- Vendor Data：厂商规格和资料

## 3. 数据元信息

每条重要数据记录 Value、Source、Timestamp、Confidence、Operator、Last Update 和 Update Status。数据状态包括 Fresh、Normal、Stale、Unknown 和 Invalid。

## 4. 数据融合与失败处理

同一个 Object 可以有 BMC、工程师和厂商资料等多个来源，系统保留来源和冲突上下文。采集任务记录目标对象、方式、状态、时间和错误信息；采集失败不能删除数据，应保留最后一次成功数据和失败原因。

## 5. 客户环境与 MVP

客户设备可以是 `OWNED`、位于 Customer DC、`NO_DIRECT_ACCESS`，数据来源为 Customer Report。第一阶段支持手工录入、Excel 导入、来源记录和历史；第二阶段支持 Redfish、IPMI、SNMP 和 Agent；第三阶段支持自动发现、质量评分和 AI 数据分析。
