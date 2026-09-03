# Atlas 工作流与状态机设计

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | 平台能力设计文档 |

## 1. 定位

Workflow 是平台能力，负责业务过程中的状态变化和任务流转，不负责资产、工单或设备主数据。

## 2. 核心模型

```text
Workflow Definition → Workflow Instance → Workflow Task → Workflow History
```

Definition 是流程模板，Instance 是一次执行，Task 是具体任务，History 记录操作者、时间、状态变化和结果。

## 3. 状态机

重要状态变化必须通过 Event → Workflow → State Change 完成，不能由页面或接口直接写状态。

资产：

```text
REQUESTED → APPROVED → ORDERED → RECEIVED
STOCK → DEPLOYING → ACTIVE → MAINTENANCE → RETIRED
```

工单：

```text
CREATED → ASSIGNED → PROCESSING → WAITING → RESOLVED → CLOSED
```

## 4. 流程示例

- 采购：申请 → 审批 → 采购 → 验收 → 入库
- 维修：故障 → 派单 → 维修 → 验证 → 关闭
- 调拨：申请 → 审批 → 运输 → 接收 → 完成

支持单级、多级和条件审批；例如按采购金额决定审批层级，按备件库存决定直接维修还是先申请备件。

## 5. 业务域关系

Asset 调用 Workflow 完成采购、验收、入库和调拨；Operations 调用 Workflow 完成派单、维修和验证；Knowledge 可在流程结束后承接解决方案。客户环境必须支持客户反馈、内部审批、现场处理和客户确认。

## 6. MVP

- 状态管理
- 简单审批
- 任务流转
- 历史记录

条件流程、多级审批、事件驱动和自动化编排后续实现。
