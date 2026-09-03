# Atlas 工作流与状态机设计

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.2 |
| 状态 | 平台能力设计文档 |

## 1. 定位

Workflow 是平台能力，负责业务过程中的任务流转、审批节点和状态变化编排，不负责资产、工单或设备主数据。

## 2. 核心模型

```text
Workflow Definition → Workflow Instance → Workflow Task → Workflow History
```

- **Workflow Definition**：流程模板，定义节点（审批/执行/通知）、边（转换条件）和参数
- **Workflow Instance**：一次执行实例，关联业务对象（采购申请/工单）
- **Workflow Task**：具体任务，分配给用户或系统执行
- **Workflow History**：历史记录，记录操作者、时间、决策和结果

## 3. 状态枚举唯一权威

**资产/工单的状态枚举唯一权威见 `docs/12-Atlas数据库模型设计.md`**：

- **对象技术状态**（objects.status）：PLANNED/ACTIVE/INACTIVE/MAINTENANCE/RETIRED
- **资产业务状态**（assets.lifecycle_status）：REQUESTED/APPROVED/ORDERED/PURCHASED/RECEIVED/STOCK/IN_TRANSIT/DEPLOYING/DEPLOYED/ACTIVE/MAINTENANCE/TRANSFERRED/RETIRED/RECOVERED
- **工单流转状态**（work_orders.status）：CREATED/ASSIGNED/PROCESSING/WAITING/SUSPENDED/RESOLVED/CLOSED/CANCELLED/REOPENED

本文档不重复定义状态枚举，专注于工作流引擎机制（流程定义、审批节点、任务分派）与状态机的联动。

## 4. 工作流引擎与状态机联动

### 4.1 设计原则

重要状态变化必须通过 **Event → Workflow → State Change** 完成，不能由页面或接口直接写状态。

```text
用户操作/系统事件 → 触发 Workflow Instance → 执行 Workflow Task → 更新业务状态 → 记录 History
```

### 4.2 联动示例

**采购审批流程**（资产状态变化）：

```text
用户提交采购申请 → REQUESTED
  ↓
创建 Workflow Instance（PURCHASE_APPROVAL）
  ↓
部门负责人审批 Task → APPROVED
  ↓
采购订单发出 → ORDERED
  ↓
供应商确认 → PURCHASED
  ↓
到货验收 → RECEIVED
  ↓
入库 → STOCK
```

**维修流程**（工单状态变化）：

```text
故障上报 → CREATED
  ↓
创建 Workflow Instance（REPAIR_APPROVAL）
  ↓
调度员派单 Task → ASSIGNED
  ↓
工程师开始处理 → PROCESSING
  ↓
等待备件 → WAITING
  ↓
备件到货继续处理 → PROCESSING
  ↓
维修完成 → RESOLVED
  ↓
客户验证通过 → CLOSED
```

### 4.3 状态变化触发规则

| 业务状态变化 | 触发 Workflow | 是否需审批 | 状态回退处理 |
| --- | --- | --- | --- |
| assets.REQUESTED → APPROVED | PURCHASE_APPROVAL | 是 | 拒绝时回到 REQUESTED |
| assets.STOCK → IN_TRANSIT | ASSET_TRANSFER | 是（调拨审批） | 取消时回到 STOCK |
| assets.ACTIVE → RETIRED | ASSET_RETIREMENT | 是 | 取消报废时 RETIRED → RECOVERED |
| work_orders.CREATED → ASSIGNED | WORKORDER_DISPATCH | 否（系统分派） | 派单失败时 → CANCELLED |
| work_orders.RESOLVED → CLOSED | WORKORDER_VERIFICATION | 否（客户确认） | 验证失败时 → REOPENED → ASSIGNED |
| work_orders.PROCESSING → SUSPENDED | WORKORDER_SUSPEND | 是（挂起审批） | 恢复时 SUSPENDED → ASSIGNED |

## 5. 流程示例

### 5.1 采购流程

```text
采购申请 → 部门负责人审批 → 采购部审批 → 采购订单 → 供应商发货 → 验收 → 入库
```

- **条件审批**：金额 < 10万元单级审批，≥ 10万元多级审批
- **状态变化**：REQUESTED → APPROVED → ORDERED → PURCHASED → RECEIVED → STOCK

### 5.2 维修流程

```text
故障上报 → 调度派单 → 工程师处理 → 备件申请（若需要）→ 维修验证 → 客户确认 → 关闭
```

- **条件流转**：有备件直接维修（PROCESSING），无备件先申请（WAITING）
- **状态变化**：CREATED → ASSIGNED → PROCESSING → WAITING → PROCESSING → RESOLVED → CLOSED

### 5.3 调拨流程

```text
调拨申请 → 审批 → 出库 → 运输 → 接收确认 → 完成
```

- **状态变化**：STOCK → IN_TRANSIT → STOCK（接收方入库）或 DEPLOYING（直接部署）

## 6. 审批节点设计

### 6.1 审批类型

- **单级审批**：一人审批即通过（如小额采购）
- **多级审批**：多人依次审批（如大额采购：申请人 → 部门负责人 → 采购负责人）
- **并行审批**：多人同时审批，全部通过才继续（如技术评审 + 财务审批）
- **条件审批**：按金额/优先级/设备类型决定审批层级

### 6.2 审批任务状态

Workflow Task 状态（workflow_task.status）：

- **PENDING**：待处理
- **COMPLETED**：已完成
- **SKIPPED**：跳过（条件不满足）
- **FAILED**：失败（审批拒绝/执行错误）

审批决策（workflow_task.decision）：

- **APPROVED**：批准
- **REJECTED**：拒绝

## 7. 业务域关系

### 7.1 Asset Domain 调用 Workflow

- 采购审批流程（PURCHASE_APPROVAL）
- 验收流程（ASSET_ACCEPTANCE）
- 入库流程（ASSET_INBOUND）
- 调拨审批流程（ASSET_TRANSFER）
- 报废审批流程（ASSET_RETIREMENT）

### 7.2 Operations Domain 调用 Workflow

- 派单流程（WORKORDER_DISPATCH）
- 维修审批流程（REPAIR_APPROVAL）
- 备件申请流程（SPARE_PART_REQUEST）
- 工单挂起审批（WORKORDER_SUSPEND）
- 客户验证流程（WORKORDER_VERIFICATION）

### 7.3 Knowledge Domain 承接流程结果

工作流结束后，可关联知识文章：

- 维修完成后自动创建故障解决方案文章
- 审批拒绝后记录决策依据

### 7.4 客户环境支持

客户环境必须支持：

- 客户反馈触发工单（CREATED）
- 内部审批后派单（ASSIGNED）
- 现场工程师处理（PROCESSING → RESOLVED）
- 客户确认验证（RESOLVED → CLOSED/REOPENED）

## 8. MVP 范围

### 8.1 核心能力

- 状态管理（状态变化通过 Workflow 触发）
- 简单审批（单级/多级审批）
- 任务流转（创建 → 分派 → 执行 → 完成）
- 历史记录（操作者、时间、决策、结果）

### 8.2 后续能力

- 条件流程（金额/优先级决定审批层级）
- 并行审批（多人同时审批）
- 事件驱动（监控告警自动创建工单）
- 自动化编排（自动派单/自动备件申请）

## 9. 设计原则

- **状态变化必须有 Workflow 记录**：直接修改状态禁止，必须通过 Workflow Instance 触发
- **审批节点必须可追溯**：记录审批人、时间、决策、意见
- **支持状态回退**：审批拒绝/客户验证失败时，状态回到前一节点
- **客户环境兼容**：无自动化能力时，人工操作仍然可以完成流程
