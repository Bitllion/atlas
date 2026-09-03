# Atlas 资产管理业务设计

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | 业务设计文档 |

## 1. 文档目的

定义 Atlas Asset Domain 的资产管理模型，包括资产生命周期、采购、验收、入库、出库、部署、维保、客户交付以及 Asset 与 Infrastructure Object 的关系。

本文档不描述数据库、API 和 UI 实现。

## 2. 资产管理定位

Atlas 资产管理不是只关注资产编号、金额、部门、负责人和折旧的传统固定资产系统。Atlas 关注：

- 基础设施实体生命周期
- 技术属性
- 部署状态
- 运维责任
- 业务归属

## 3. Asset Domain 核心目标

Asset Domain 负责回答：

- 这个设备是谁的？（Ownership）
- 它从哪里来？（采购、供应商、合同、订单）
- 它现在在哪里？（数据中心、机房、机柜、客户现场）
- 它当前是什么状态？（库存、待部署、使用中、维修、报废）
- 谁负责维护？（内部团队、供应商、客户）

## 4. Asset 与 Infrastructure Object

Asset Record 描述商业属性、生命周期和责任关系；Object 描述真实设备、技术属性和拓扑关系。

```text
Asset Record ↔ Infrastructure Object
```

例如 GPU 对象：

```yaml
Object:
  id: GPU-B300-001
  model: B300
  firmware: 97.xx
  uuid: xxxx
```

资产记录：

```yaml
Asset Record:
  asset_no: AST-GPU-00001
  purchase_date: 2026-01
  vendor: NVIDIA
  warranty_until: 2029-01
```

资产编号、设备序列号和 Object ID 不得混用。

## 5. 资产生命周期

```text
需求申请 → 采购审批 → 采购执行 → 到货 → 验收 → 入库
→ 部署 → 使用 → 维修 → 调拨 → 报废
```

每个阶段应有状态、责任人、时间、关联对象和审计记录。

## 6. 采购管理

采购过程包括采购申请、审批、供应商、型号、数量和预算。

采购不是直接创建 Object，正确顺序是：

```text
采购申请 → 采购订单 → 到货 → 验收 → 创建 Object → 生成 Asset
```

申请示例：GPU 服务器、GB300、数量 10、供应商 NVIDIA；审批可经过申请人、部门负责人和采购负责人。

## 7. 到货验收

验收用于确认设备符合采购要求。

基础信息：型号、SN、PN、数量。

技术信息：CPU、GPU、Memory、NIC、Firmware。

文档信息：Datasheet、测试报告、保修资料。

验收完成后创建 Infrastructure Object，并生成 Asset Record。

## 8. 入库与出库

入库表示设备进入企业资产管理范围，状态通常为：

```text
RECEIVED → STOCK
```

入库需记录仓库、位置、管理员和时间。

出库表示资产离开库存进入运输或部署流程，不等于绑定机架位置：

```text
出库申请 → 审批 → 资产出库 → 运输 → 接收确认
```

## 9. 部署与客户交付

部署用于记录设备实际运行位置：

```text
Asset → Deployment → Infrastructure Location
```

客户租赁场景示例：

```yaml
asset: GB300 Rack-001
ownership: OWNED_BY_ATLAS
location: CUSTOMER_DATACENTER
usage: CUSTOMER
management_scope: HARDWARE_ONLY
maintenance: ATLAS_TEAM
```

所有权不等于部署位置，使用方不等于维护责任方。

## 10. 资产生命周期状态

资产业务状态（assets.lifecycle_status）用于表达资产从申请到报废的完整流转过程，权威定义见 `docs/12-Atlas数据库模型设计.md`，状态枚举如下：

| 状态 | 说明 | 适用场景 |
| --- | --- | --- |
| REQUESTED | 已申请 | 采购申请已创建 |
| APPROVED | 已批准 | 采购申请已审批通过 |
| ORDERED | 已下单 | 采购订单已发出 |
| PURCHASED | 已采购 | 供应商确认订单 |
| RECEIVED | 已到货 | 设备已到达验收区 |
| STOCK | 库存中 | 设备已入库 |
| IN_TRANSIT | 运输中 | 设备已出库运输（出库后→接收前） |
| DEPLOYING | 部署中 | 设备正在安装 |
| DEPLOYED | 已部署 | 设备已安装未激活 |
| ACTIVE | 使用中 | 设备正常运行 |
| MAINTENANCE | 维护中 | 设备维修或保养 |
| TRANSFERRED | 已调拨 | 设备转移到其他位置 |
| RETIRED | 已退役 | 设备报废 |
| RECOVERED | 退役撤销 | 退役后重新激活（退役后被 Agent 重新发现或取消报废） |

### 10.1 状态机模型

完整状态转换关系（ASCII 图）：

```text
REQUESTED → APPROVED → ORDERED → PURCHASED → RECEIVED → STOCK
                                                           ↓
                                                      IN_TRANSIT
                                                           ↓
                                                       DEPLOYING
                                                           ↓
                                                        DEPLOYED
                                                           ↓
                          ┌───────────────────────────> ACTIVE <───────────┐
                          │                                ↓                │
                          │                           MAINTENANCE           │
                          │                                ↓                │
                          │                         TRANSFERRED/RETIRED     │
                          │                                                 │
                          └─────────────────────────── RECOVERED ───────────┘
```

### 10.2 关键路径说明

**正常采购-部署路径**：  
`REQUESTED → APPROVED → ORDERED → PURCHASED → RECEIVED → STOCK → IN_TRANSIT → DEPLOYING → DEPLOYED → ACTIVE`

**库存回退路径**：  
设备从 STOCK 出库运输时进入 IN_TRANSIT，若接收方确认到货并准备安装，进入 DEPLOYING；若部署取消，可回到 STOCK（需记录 inventory_records 中的出入库事务）。

**维护路径**：  
`ACTIVE → MAINTENANCE`（维修或保养）→ `ACTIVE`（恢复运行）  
部件更换时，旧部件状态可变更为 `RETIRED`（报废）或 `TRANSFERRED`（返厂/入库），具体路径由 `replacement_events.old_object_disposition` 字段决定（RETIRED/RMA/STOCK/SCRAPPED）。

**调拨路径**：  
`ACTIVE/STOCK → TRANSFERRED`（调拨至其他位置）→ `STOCK`（接收方入库）或 `DEPLOYING`（直接部署）

**退役与撤销路径**：  
`ACTIVE/MAINTENANCE → RETIRED`（设备报废）  
`RETIRED → RECOVERED`（退役撤销：客户取消报废决策，或 Agent 重新发现设备仍在运行）→ `ACTIVE/STOCK`

### 10.3 状态转换条件

| 转换 | 触发事件 | 需审批 | 记录位置 |
| --- | --- | --- | --- |
| REQUESTED → APPROVED | 采购审批通过 | 是 | workflow_instance/purchase_requests |
| APPROVED → ORDERED | 采购订单发出 | 否 | purchase_orders |
| PURCHASED → RECEIVED | 供应商发货确认到货 | 否 | assets.received_date |
| RECEIVED → STOCK | 验收通过入库 | 否 | inventory_records |
| STOCK → IN_TRANSIT | 出库运输 | 是 | inventory_records |
| IN_TRANSIT → DEPLOYING | 到达现场开始安装 | 否 | deployments |
| DEPLOYING → DEPLOYED | 物理安装完成 | 否 | deployments |
| DEPLOYED → ACTIVE | 设备上线激活 | 否 | objects.status |
| ACTIVE → MAINTENANCE | 故障或计划维护 | 否 | work_orders |
| MAINTENANCE → ACTIVE | 维修完成验证通过 | 否 | repair_records |
| ACTIVE → TRANSFERRED | 调拨申请批准 | 是 | workflow_instance |
| TRANSFERRED → STOCK | 接收方入库确认 | 否 | inventory_records |
| ACTIVE → RETIRED | 报废申请批准 | 是 | workflow_instance |
| RETIRED → RECOVERED | 取消报废或 Agent 重新发现 | 是 | object_history |

### 10.4 边界场景处理

**已接收未部署**：  
设备验收完成后有两条路径：
- 直接入库 STOCK（通用场景）
- 直接运输部署 IN_TRANSIT（紧急项目）

**部件更换旧件处理**：  
旧部件状态变更由 `replacement_events.old_object_disposition` 决定：
- RETIRED：直接报废
- RMA：返厂维修（状态为 MAINTENANCE → RETIRED/RECOVERED）
- STOCK：回库存
- SCRAPPED：物理销毁

**退役后重新发现**：  
当设备状态为 RETIRED 时，若 Agent 仍能采集到设备数据（说明设备未物理移除），系统应：
1. 生成告警：设备已标记退役但仍在运行
2. 人工确认：是否取消退役（RETIRED → RECOVERED → ACTIVE）或更新位置信息（设备可能已转移）

## 11. 维保、调拨与报废

维保管理包括维保商、保修期限、服务等级、联系方式和合同，例如 NVIDIA、2026—2029、Gold。

调拨必须记录原位置、新位置、时间、审批和责任人。

报废流程为：报废申请 → 审批 → 状态更新 → 历史保存。报废不是删除 Object，Object 历史必须保留。

## 12. Asset 与 Operations

资产状态变化可以由运维事件触发：

```text
GPU 故障 → Operations Work Order → 维修 → Asset 状态更新
```

## 13. MVP 范围

- 采购申请、审批和订单
- 到货验收并创建 Object
- 入库、库存和出库流程
- 部署位置
- 资产状态、维保和生命周期

## 14. 设计原则

- Asset 与 Object 分离。
- 支持自有机房、客户机房和第三方环境。
- 无网络、无 BMC 或无带内权限时，资产仍然存在并可管理。
- 资产变化必须可追踪。
