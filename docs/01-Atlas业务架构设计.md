# Atlas 业务架构设计

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | 业务架构设计文档 |

## 1. 文档目的

本文档用于定义 Atlas 平台的整体业务架构，主要描述：

- Atlas 的业务组成
- 各业务域职责
- 业务域之间的关系
- 核心业务流程
- 平台能力边界

本文档不描述：

- 数据库详细设计
- API 详细设计
- 页面实现

相关基础设计：

- `docs/00-产品定义.md`：产品定位与总体定义
- `docs/02-基础设施对象模型.md`：基础设施对象如何表达现实世界
- 资源关系、资产生命周期和运维流程将在后续专项文档中细化

## 2. Atlas 业务定位

Atlas 是面向 AI 数据中心、高性能计算环境以及企业级基础设施环境的智能运营管理平台。

Atlas 的核心目标是：

> 通过建立基础设施数字化模型，实现资产管理、运维管理以及基础设施运营能力的一体化。

Atlas 管理的对象包括：

- IT 计算资源
- 网络资源
- 机房基础设施
- 资产信息
- 运维活动
- 知识经验

Atlas 必须支持以下真实企业环境：

- 自有数据中心
- 客户数据中心
- 第三方托管环境
- 多组织、多地点、多权限场景

## 3. Atlas 整体业务架构

Atlas 采用分层架构。上层业务能力通过统一的 Infrastructure Core 协同，底层通过多种数据接入方式获得信息。

```text
Atlas
│
├── 业务应用层
│   ├── Dashboard
│   ├── CMDB
│   ├── Asset
│   ├── Operations
│   └── Knowledge
│
├── 业务能力层
│   ├── Asset Domain
│   ├── Operations Domain
│   └── Knowledge Domain
│
├── 平台能力层
│   ├── Workflow Engine
│   ├── Permission
│   ├── Notification
│   ├── Audit
│   └── Search
│
├── Infrastructure Core
│   ├── Object
│   ├── Relationship
│   ├── Specification
│   ├── Data Source
│   └── History
│
└── 数据接入层
    ├── Discovery
    ├── Import
    ├── Vendor Data
    ├── Customer Data
    └── Manual Input
```

## 4. Atlas 核心理念

### 4.1 基础设施对象作为统一业务基础

Atlas 不直接围绕资产表设计。所有基础设施实体首先成为 `Infrastructure Object`，例如：

- GB300 服务器
- GPU
- BF3 网卡
- 交换机
- 机柜
- CDU

所有业务能力都通过 Object 进行关联。

### 4.2 一个对象，多种业务视角

同一个基础设施对象可以被不同业务使用。例如 GB300 服务器：

资产视角：

- 资产编号
- 采购日期
- 供应商
- 合同
- 维保期限

运维视角：

- 故障记录
- 维修记录
- 巡检记录
- 当前状态

技术视角：

- GPU 数量
- Firmware
- BMC
- PCI 信息

### 4.3 对象、资产和业务记录分离

- Infrastructure Object：表示真实世界中的基础设施实体
- Asset Record：表示资产编号、采购、供应商、维保等管理信息
- Business Record：表示工单、巡检、维修等业务过程数据

Asset 不是 Object，Operations Record 也不是 Object，但它们必须能够关联到一个或多个 Infrastructure Object。

## 5. 业务域设计

Atlas 当前包含三个主要业务域：

- Asset Domain
- Operations Domain
- Knowledge Domain

同时提供 Workflow、Permission、Notification、Audit、Automation Capability 等平台能力。

### 5.1 Asset Domain：资产管理域

#### 业务目标

负责管理基础设施资产生命周期，回答：

- 资产从哪里来？
- 当前属于谁？
- 部署在哪里？
- 状态如何变化？
- 是否需要维护？

#### 管理范围

采购阶段：

- 采购申请
- 审批
- 供应商
- 合同
- 到货

入库阶段：

- 到货验收
- 资产编号
- 初始化信息

部署阶段：

- 分配位置
- 关联基础设施对象
- 记录所有权、使用方和管理范围

使用阶段：

- 状态管理
- 维保管理
- 客户交付管理

生命周期结束：

- 调拨
- 退役
- 报废

#### Asset 与 Object 的关系

Asset Record 与 Infrastructure Object 分离：

```text
Infrastructure Object
        │
        └── Asset Record
```

例如：

```yaml
Object:
  id: GPU-B300-001
  type: GPU

Asset Record:
  asset_no: AST-000001
  purchase_date: 2026-01
  vendor: NVIDIA
  warranty_until: 2028-01
```

### 5.2 Operations Domain：运维管理域

#### 业务目标

负责基础设施运行过程中的维护和保障，回答：

- 设备是否正常？
- 出现问题如何处理？
- 谁负责处理？
- 历史是否可追踪？

#### 管理范围

工单管理：

- 故障工单
- 维修工单
- 巡检工单
- 变更工单

维护管理：

- 更换部件
- 固件升级记录
- 检查记录
- 现场服务记录

状态管理示例：

- 正常
- 故障
- 维修中
- 退役

#### 运维对象关联

所有运维活动必须关联 Infrastructure Object，必要时同时关联其父级对象和位置关系：

```text
维修工单
    │
    └── GPU-B300-001
            │
            └── GB300 Server
                    │
                    └── Rack
```

### 5.3 Knowledge Domain：知识管理域

#### 业务目标

沉淀基础设施相关知识，包括：

- 厂商文档
- 技术手册
- SOP
- 故障案例
- 维修经验

#### 知识关联

知识不应只是普通文档，应能关联对象、历史和运维记录：

```text
Knowledge
    │
    ├── Infrastructure Object
    ├── History
    └── Operations Record
```

例如 B300 Firmware 升级文档可以关联：

- GPU：B300
- Firmware 版本
- 历史升级记录
- 维修案例

## 6. 平台能力设计

以下能力属于平台服务，不作为独立的一级业务域。

### 6.1 Workflow Engine：流程引擎

负责：

- 审批
- 状态流转
- 流程编排

采购流程示例：

```text
申请 → 审批 → 采购 → 验收 → 入库
```

维修流程示例：

```text
故障 → 派单 → 维修 → 验证 → 关闭
```

Workflow 负责流程状态和流转，不直接承载资产、对象或工单的业务主数据。

### 6.2 Permission：权限管理

Atlas 需要支持：

- 用户权限
- 角色权限
- 客户隔离
- 数据访问范围
- 管理范围与操作权限

必须特别考虑：设备可能属于企业、部署在客户环境、客户负责带内操作，而企业只负责硬件维护。

### 6.3 Notification：通知

负责向相关用户、组织或服务团队发送：

- 工单分派通知
- 审批通知
- 故障通知
- 维保到期提醒
- 客户交付状态通知

### 6.4 Audit：审计

记录关键业务操作和数据变化，包括：

- 谁执行了操作
- 操作对象是什么
- 发生了什么变化
- 变化发生的时间
- 操作来源和结果

### 6.5 Search：搜索

搜索应围绕基础设施对象、资产、关系、工单、知识和历史记录提供统一查询能力。

### 6.6 Data Source Management：数据来源管理

Atlas 支持多来源数据：

- 自动采集
- 人工录入
- 客户反馈
- 厂商资料
- 文件导入

重要数据需要记录：

- 来源
- 时间
- 更新时间
- 更新状态
- 可信度
- 访问能力

### 6.7 Automation Capability：自动化能力

自动化属于扩展能力，未来可支持：

- PXE
- DHCP
- Firmware 管理
- 硬件扫描
- 批量验证

自动化能力依赖：

- 网络环境
- 设备权限
- 管理范围
- 客户授权

不是所有设备默认支持自动化，也不能默认所有设备可访问、可 SSH 或可执行命令。

## 7. 典型业务场景

### 7.1 采购新 GB300

```text
采购申请
    ↓
审批
    ↓
到货验收
    ↓
创建 Infrastructure Object
    ↓
生成 Asset Record
    ↓
关联部署位置
    ↓
进入生命周期管理
```

### 7.2 客户租赁部署

设备信息：

```yaml
asset: GB300 Rack
ownership: OURS
location: CUSTOMER_DATACENTER
usage: CUSTOMER
maintenance: OURS
```

Atlas 需要记录：

- 资产信息
- 部署位置
- 使用方
- 管理范围
- 维保责任
- 客户隔离边界

### 7.3 GPU 故障维修

```text
发现故障
    ↓
创建工单
    ↓
关联 GPU 对象
    ↓
现场维修
    ↓
更换部件
    ↓
更新对象关系
    ↓
记录历史
```

客户环境下，故障可能来自客户反馈，而不是自动采集；维修流程也可能由现场工程师完成。两者都属于 Operations Domain。

## 8. MVP 业务范围

### 第一阶段：Atlas Core

实现：

- 基础设施对象
- 对象关系
- 属性管理
- 数据来源
- 历史记录

### 第二阶段：Asset MVP

实现：

- 采购
- 验收
- 入库
- 出库
- 部署位置
- 生命周期

### 第三阶段：Operations MVP

实现：

- 工单
- 巡检
- 维修
- 变更
- 部件更换和历史追踪

### 第四阶段：Knowledge

实现：

- 文档管理
- SOP
- 故障知识库
- 对象与运维记录关联

### 后续扩展：Automation

基于 Infrastructure Core、Data Source 和 Permission 实现：

- 自动发现
- PXE
- Firmware 管理
- 自动验证

## 9. 架构总结

Atlas 最终形成以下结构：

```text
业务应用层
├── Asset
├── Operations
└── Knowledge

平台能力层
├── Workflow
├── Permission
├── Notification
├── Audit
└── Search

核心模型层
├── Infrastructure Object
├── Relationship
├── Specification
├── Data Source
└── History
```

Atlas 的核心价值是：

> 管理属于企业的基础设施资源，无论资源位于何处、由谁使用、采用何种数据来源，都能够形成统一的数字化管理体系。

后续对象模型设计必须遵循以下关系：

- 业务依赖 Object
- Asset 不等于 Object
- Operations 不等于 Object
- Knowledge 也必须能够绑定 Object
