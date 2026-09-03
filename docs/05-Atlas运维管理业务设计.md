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

## 4. 工单状态机模型

工单状态（work_orders.status）表示运维任务流转过程，权威定义见 `docs/12-Atlas数据库模型设计.md`，状态枚举如下：

| 状态 | 说明 | 适用场景 |
| --- | --- | --- |
| CREATED | 已创建 | 工单刚创建，待分派 |
| ASSIGNED | 已分派 | 工单已指派工程师 |
| PROCESSING | 处理中 | 工程师正在处理 |
| WAITING | 等待中 | 等待备件或客户响应（可恢复） |
| SUSPENDED | 已挂起 | 工单暂停（备件不足/客户拒绝/等待维护窗口） |
| RESOLVED | 已解决 | 工程师完成处理，待客户验证 |
| CLOSED | 已关闭 | 客户验证通过，工单完成 |
| CANCELLED | 已取消 | 派单失败/客户拒绝/申请撤销 |
| REOPENED | 已重开 | 客户验证不通过或故障复发 |

### 4.1 状态机模型

完整状态转换关系（ASCII 图）：

```text
                      CREATED
                         ↓
                      ASSIGNED ←─────────────┐
                         ↓                   │
                    PROCESSING               │ (重新派单)
                    ↙    ↓    ↘             │
              WAITING  RESOLVED  SUSPENDED   │
                 ↓        ↓         ↓        │
            PROCESSING  CLOSED  CANCELLED    │
                         ↓                   │
                      REOPENED ──────────────┘
```

### 4.2 关键路径说明

**正常流转路径**：  
`CREATED → ASSIGNED → PROCESSING → RESOLVED → CLOSED`

**等待路径**：  
`PROCESSING → WAITING`（等待备件到货/客户提供信息）→ `PROCESSING`（恢复处理）

**挂起路径**：  
`ASSIGNED/PROCESSING → SUSPENDED`（备件长期缺货/客户维护窗口未到/客户拒绝进场）  
`SUSPENDED → ASSIGNED`（重新分配工程师）或 `CANCELLED`（取消工单）

**取消路径**：  
`CREATED/ASSIGNED → CANCELLED`（派单失败/客户撤销申请/设备已退役）

**重开路径**：  
`CLOSED → REOPENED`（客户验证不通过/故障复发）→ `ASSIGNED`（重新派单）

### 4.3 状态转换条件

| 转换 | 触发事件 | 操作者 | 记录位置 |
| --- | --- | --- | --- |
| CREATED → ASSIGNED | 派单分配工程师 | 调度员/系统 | work_orders.assigned_to |
| ASSIGNED → PROCESSING | 工程师开始处理 | 工程师 | work_orders.updated_at |
| PROCESSING → WAITING | 等待备件或客户响应 | 工程师 | work_orders.status + 备注 |
| WAITING → PROCESSING | 备件到货或客户响应 | 工程师 | work_orders.updated_at |
| PROCESSING → RESOLVED | 处理完成 | 工程师 | work_orders.resolved_at |
| RESOLVED → CLOSED | 客户验证通过 | 客户/调度员 | work_orders.closed_at |
| CLOSED → REOPENED | 客户验证不通过/故障复发 | 客户/系统 | work_orders.updated_at |
| REOPENED → ASSIGNED | 重新派单 | 调度员 | work_orders.assigned_to |
| ASSIGNED → SUSPENDED | 挂起工单（备件不足/窗口未到） | 调度员/工程师 | work_orders.status + 备注 |
| SUSPENDED → ASSIGNED | 恢复派单 | 调度员 | work_orders.assigned_to |
| SUSPENDED → CANCELLED | 取消挂起工单 | 调度员 | work_orders.updated_at |
| CREATED/ASSIGNED → CANCELLED | 派单失败/客户撤销 | 调度员/客户 | work_orders.updated_at |

### 4.4 回到 ASSIGNED 重新派单的状态

以下状态可回到 ASSIGNED 重新派单：
- **REOPENED**：客户验证不通过或故障复发，需重新分配工程师
- **SUSPENDED**：挂起工单恢复后，可重新分配工程师（原工程师可能已离职或调岗）

**注意**：WAITING 状态不需要重新派单，工程师继续处理即可（WAITING → PROCESSING）。

### 4.5 边界场景处理

**WAITING vs SUSPENDED**：
- WAITING：短期等待（几小时到1-2天），工程师继续跟进，工单仍属于该工程师
- SUSPENDED：长期暂停（数天到数周），工单可能重新分配，需要审批恢复

**CANCELLED vs CLOSED**：
- CANCELLED：工单未完成即终止（客户拒绝/派单失败/申请撤销）
- CLOSED：工单正常完成并验证通过

**REOPENED 处理**：
- 若故障复发且原工程师在岗，可直接 REOPENED → PROCESSING（系统自动重新分配给原工程师）
- 若原工程师不可用，必须 REOPENED → ASSIGNED（人工重新派单）

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
