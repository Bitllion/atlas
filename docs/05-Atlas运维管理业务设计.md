# Atlas 运维管理业务设计

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | 业务设计文档 |

## 1. 文档目的

定义 Operations Domain 的运维目标、工单、故障、巡检、维修、部件更换、维护历史和客户环境运维场景。本文件不描述数据库、API 和前端实现。

## 2. 运维定位

Atlas 运维不是传统 ITSM，不负责服务器 OS、应用、日志和网络服务的全面管理，而是管理 AI 基础设施硬件生命周期中的运维活动。

核心目标：

> 管理 AI 基础设施从发现问题到恢复运行的完整过程。

## 3. 核心能力

- 故障管理：故障位置、影响范围和责任人
- 工单管理：任务流转、执行人和完成时间
- 维修管理：维修内容、更换部件和验证结果
- 巡检管理：主动发现风险
- 维护历史：设备过去发生过什么

所有运维记录必须关联 Infrastructure Object。

## 4. 工单模型

Work Order 表示一次明确的运维任务，基本属性包括 Work Order ID、Title、Type、Priority、Status、Created Time、Owner、Executor 和 Related Object。

工单类型包括故障、维修、巡检和变更。通用生命周期为：

```text
Created → Assigned → Processing → Waiting → Resolved → Closed
```

## 5. 故障与维修

故障来源可以是 BMC、Redfish、IPMI、监控、工程师、客户反馈、现场巡检或厂商通告。记录 Fault ID、Object、Fault Type、Severity、Description、Evidence 和 Time。

维修流程：

```text
故障确认 → 创建维修任务 → 准备备件 → 现场维修 → 测试验证 → 关闭工单
```

部件替换必须记录 Old Object、New Object、Time、Engineer 和 Reason，并结束旧关系、创建新关系、保留完整历史。

## 6. 巡检、维保与客户环境

巡检对象包括 Rack、Server、GPU、CDU 和 Power Shelf。检查内容可包含温度、Firmware、BMC、流量、压力和告警。对象应关联 Maintenance Owner、Vendor、Warranty、SLA 和 Contact。

自有机房可以自动发现；客户机房可能只能由客户反馈后安排工程师现场处理。两种流程都属于 Operations，不能假设所有设备可自动采集或自动修复。

## 7. MVP

- 创建、分派、流转和关闭工单
- 故障记录与对象关联
- 维修记录和更换记录
- 巡检任务和巡检记录
- 设备状态及维护历史
