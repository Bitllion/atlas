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

## 10. 资产状态

通用状态：

```text
PURCHASED → RECEIVED → STOCK → DEPLOYING → ACTIVE
                                      ↓
                               MAINTENANCE
                                      ↓
                         TRANSFERRED / RETIRED
```

资产域可扩展库存、待部署、使用中和报废等业务状态；运维域可扩展正常、故障和维修中等状态。

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
