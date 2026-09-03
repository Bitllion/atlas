# Atlas 数据库模型设计

| 项目 | 内容 | 修订说明 |
| --- | --- | --- |
| 版本 | v0.2 | 基于架构评审补全字段级设计 |
| 状态 | 数据库设计文档 | - |

## 修订说明

本版本基于架构评审报告，主要变更包括：

- 补全所有表的字段级定义，支持 Alembic migration 直接开发
- 统一三层状态枚举（对象技术状态、资产业务状态、工单流转状态）
- 补充 ownership 枚举与多组织字段（owner/operator/maintainer）
- 补充软删除字段（deleted_at/deleted_by）与乐观锁（version）
- 补充数据治理字段（data_source、confidence、data_status）
- 补充关系模型约束（allowed_types、is_directed、attributes_schema）
- 补充采集治理表（agents、collection_jobs、collection_failures）
- 补充幂等性表（idempotency_keys）
- 明确高频查询字段结构化规则与 JSONB 索引策略
- 完善审计日志字段定义
- 新增 user_resource_grants 跨组织授权表（来自 docs/08 7.1）

---

## 1. 数据库设计规范

### 1.1 软删除规范

所有核心业务表（objects、relationships、assets、work_orders、object_specs、object_history、knowledge_articles 等）禁止物理删除，必须使用软删除：

- 补充字段：`deleted_at TIMESTAMP NULL`、`deleted_by UUID NULL`
- 删除操作：`UPDATE table SET deleted_at = NOW(), deleted_by = :user_id WHERE id = :id`
- 查询过滤：**所有查询默认添加 `WHERE deleted_at IS NULL`**
- 恢复操作：`UPDATE table SET deleted_at = NULL, deleted_by = NULL WHERE id = :id`

### 1.2 乐观锁规范

高并发修改的核心表（objects、assets、work_orders）必须使用乐观锁防止并发冲突：

- 补充字段：`version INT NOT NULL DEFAULT 1`
- 更新操作：`UPDATE table SET field = :value, version = version + 1 WHERE id = :id AND version = :expected_version`
- 冲突处理：如果更新返回 0 行，抛出 `ConcurrentModificationError`

### 1.3 索引策略

- **主键索引**：所有表的 `id` 字段自动创建主键索引
- **外键索引**：所有外键字段（如 `object_id`、`organization_id`）创建普通索引
- **查询索引**：高频查询字段（如 `status`、`object_type_id`、`owner_org_id`）创建联合索引
- **JSONB 索引**：`spec_data`、`attributes` 等 JSONB 字段创建 GIN 索引：`CREATE INDEX idx_object_specs_data ON object_specs USING GIN (spec_data);`
- **软删除索引**：`deleted_at` 字段创建部分索引：`CREATE INDEX idx_table_active ON table (id) WHERE deleted_at IS NULL;`

### 1.4 History 分区建议

`object_history` 表预期快速增长（每次采集/修改产生记录），建议按月分区：

```sql
CREATE TABLE object_history (
  id UUID PRIMARY KEY,
  ...
  created_at TIMESTAMP NOT NULL
) PARTITION BY RANGE (created_at);

CREATE TABLE object_history_2026_09 PARTITION OF object_history
  FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
```

### 1.5 JSONB 使用原则

- **核心查询字段必须结构化**：firmware_version、hardware_generation、memory_gb、core_count 等
- **JSONB 只放差异属性**：不同设备类型特有的、低频查询的扩展属性
- **JSONB 内容必须有 Schema 约束**：在 `object_types` 表的 `schema` 字段定义 JSON Schema

---

## 2. 状态枚举定义

### 2.1 对象技术状态（objects.status）

| 状态 | 说明 | 适用场景 |
| --- | --- | --- |
| PLANNED | 计划中 | 设备已采购但未到货 |
| ACTIVE | 活跃 | 设备正常运行 |
| INACTIVE | 非活跃 | 设备已下线但未退役 |
| MAINTENANCE | 维护中 | 设备正在维修或升级 |
| RETIRED | 已退役 | 设备已报废或回收 |

### 2.2 资产业务状态（assets.lifecycle_status）

| 状态 | 说明 | 适用场景 |
| --- | --- | --- |
| REQUESTED | 已申请 | 采购申请已创建 |
| APPROVED | 已批准 | 采购申请已审批通过 |
| ORDERED | 已下单 | 采购订单已发出 |
| PURCHASED | 已采购 | 供应商确认订单 |
| RECEIVED | 已到货 | 设备已到达验收区 |
| STOCK | 库存中 | 设备已入库 |
| IN_TRANSIT | 运输中 | 设备已出库运输 |
| DEPLOYING | 部署中 | 设备正在安装 |
| DEPLOYED | 已部署 | 设备已安装未激活 |
| ACTIVE | 使用中 | 设备正常运行 |
| MAINTENANCE | 维护中 | 设备维修或保养 |
| TRANSFERRED | 已调拨 | 设备转移到其他位置 |
| RETIRED | 已退役 | 设备报废 |
| RECOVERED | 退役撤销 | 退役后重新激活 |

### 2.3 工单流转状态（work_orders.status）

| 状态 | 说明 | 适用场景 |
| --- | --- | --- |
| CREATED | 已创建 | 工单刚创建 |
| ASSIGNED | 已分派 | 工单已指派工程师 |
| PROCESSING | 处理中 | 工程师正在处理 |
| WAITING | 等待中 | 等待备件或客户响应 |
| SUSPENDED | 已挂起 | 工单暂停（备件不足/客户拒绝） |
| RESOLVED | 已解决 | 工程师完成处理 |
| CLOSED | 已关闭 | 客户验证通过 |
| CANCELLED | 已取消 | 工单取消 |
| REOPENED | 已重开 | 客户验证不通过重新打开 |

### 2.4 所有权枚举（objects.ownership）

| 值 | 说明 |
| --- | --- |
| OWNED | 自有资产 |
| CUSTOMER_OWNED | 客户资产 |
| THIRD_PARTY | 第三方资产 |

### 2.5 管理范围枚举（objects.management_scope）

| 值 | 说明 |
| --- | --- |
| FULL_CONTROL | 完全控制（硬件+OS+应用） |
| HARDWARE_ONLY | 仅硬件管理 |
| MAINTENANCE_ONLY | 仅维护权限 |
| NO_ACCESS | 无访问权限 |

### 2.6 数据状态枚举（object_specs.data_status）

| 值 | 说明 |
| --- | --- |
| FRESH | 新鲜（< 5 分钟） |
| NORMAL | 正常（< 1 小时） |
| STALE | 过期（> 1 小时） |
| UNKNOWN | 未知（从未采集） |
| INVALID | 无效（采集失败） |

---

## 3. Core 核心表

### 3.1 objects 表

基础设施对象核心表，所有物理/逻辑资源的统一模型。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 对象唯一标识 |
| object_type_id | UUID | FK, NOT NULL | 对象类型（FK to object_types） |
| name | VARCHAR(255) | NOT NULL | 对象名称 |
| serial_number | VARCHAR(255) | NULL | 设备序列号（厂商SN） |
| asset_number | VARCHAR(255) | NULL | 资产编号（企业内部） |
| uuid | VARCHAR(255) | NULL | 设备UUID（GPU/NIC等） |
| manufacturer | VARCHAR(255) | NULL | 制造商 |
| model | VARCHAR(255) | NULL | 型号 |
| firmware_version | VARCHAR(100) | NULL | 固件版本（高频查询字段） |
| hardware_generation | VARCHAR(100) | NULL | 硬件代数（如B300/H100） |
| status | VARCHAR(50) | NOT NULL | 对象技术状态（枚举见2.1） |
| ownership | VARCHAR(50) | NOT NULL | 所有权（枚举见2.4） |
| management_scope | VARCHAR(50) | NOT NULL | 管理范围（枚举见2.5） |
| owner_org_id | UUID | FK, NULL | 所有者组织（FK to organizations） |
| operator_org_id | UUID | FK, NULL | 运营者组织（FK to organizations） |
| maintainer_org_id | UUID | FK, NULL | 维护者组织（FK to organizations） |
| deployed_location_id | UUID | FK, NULL | 部署位置（FK to objects，位置也是对象） |
| version | INT | NOT NULL, DEFAULT 1 | 乐观锁版本号 |
| deleted_at | TIMESTAMP | NULL | 软删除时间 |
| deleted_by | UUID | NULL | 软删除操作者 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |
| created_by | UUID | NULL | 创建者（FK to users） |
| updated_by | UUID | NULL | 更新者（FK to users） |

**索引**：
- `idx_objects_type_status ON (object_type_id, status) WHERE deleted_at IS NULL`
- `idx_objects_owner_org ON (owner_org_id) WHERE deleted_at IS NULL`
- `idx_objects_serial ON (serial_number) WHERE deleted_at IS NULL`
- `idx_objects_firmware ON (firmware_version) WHERE deleted_at IS NULL`

**核心字段结构化规则**：

| object_type | 必须结构化字段 | 说明 |
| --- | --- | --- |
| GPU | firmware_version, hardware_generation | 用于批量升级查询 |
| SERVER | firmware_version, hardware_generation | 用于型号统计 |
| NIC | firmware_version | 用于固件一致性检查 |
| CDU | hardware_generation | 用于冷却能力分类 |

### 3.2 object_types 表

对象类型定义表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 类型唯一标识 |
| name | VARCHAR(100) | NOT NULL, UNIQUE | 类型名称（如SERVER/GPU/RACK） |
| category | VARCHAR(100) | NOT NULL | 类型分类（IT/NETWORK/FACILITY/POWER） |
| description | TEXT | NULL | 类型说明 |
| schema | JSONB | NULL | JSONB 字段的 JSON Schema 定义 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**初始数据**：
- DATACENTER, ROOM, RACK, SERVER, GPU_SERVER, GPU, CPU, MEMORY, STORAGE, NIC
- SWITCH, PORT, LINK, TRANSCEIVER
- CDU, COOLING_SYSTEM, PDU, UPS, POWER_SHELF, POWER_MODULE, PSU

### 3.3 object_specs 表

对象技术规格表，记录设备详细配置信息。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 规格记录唯一标识 |
| object_id | UUID | FK, NOT NULL | 关联对象（FK to objects） |
| spec_data | JSONB | NOT NULL | 技术规格数据（JSONB） |
| data_source | VARCHAR(100) | NOT NULL | 数据来源（DISCOVERY/MANUAL/IMPORT/DOCUMENT/CUSTOMER_REPORT/VENDOR） |
| confidence | VARCHAR(50) | NOT NULL | 数据可信度（HIGH/MEDIUM/LOW） |
| data_status | VARCHAR(50) | NOT NULL | 数据状态（枚举见2.6） |
| operator_id | UUID | NULL | 操作者（FK to users） |
| last_successful_update | TIMESTAMP | NULL | 最后成功更新时间 |
| version | INT | NOT NULL, DEFAULT 1 | 规格版本号 |
| deleted_at | TIMESTAMP | NULL | 软删除时间 |
| deleted_by | UUID | NULL | 软删除操作者 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引**：
- `idx_object_specs_object ON (object_id) WHERE deleted_at IS NULL`
- `idx_object_specs_data ON spec_data USING GIN` （JSONB GIN 索引）
- `idx_object_specs_status ON (data_status, last_successful_update)`

**spec_data JSONB 示例**（GPU）：
```json
{
  "memory_gb": 288,
  "cuda_cores": 16896,
  "nvlink_version": "5.0",
  "pci_bdf": "0000:41:00.0",
  "gpu_uuid": "GPU-xxxxx",
  "hbm_bandwidth_gbps": 8000
}
```

### 3.4 relationships 表

对象关系表，表达对象之间的连接关系。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 关系唯一标识 |
| source_object_id | UUID | FK, NOT NULL | 源对象（FK to objects） |
| relation_type_id | UUID | FK, NOT NULL | 关系类型（FK to relationship_types） |
| target_object_id | UUID | FK, NOT NULL | 目标对象（FK to objects） |
| attributes | JSONB | NULL | 关系属性（如Speed/Protocol/FlowRate） |
| status | VARCHAR(50) | NOT NULL | 关系状态（ACTIVE/INACTIVE/REMOVED） |
| confidence | VARCHAR(50) | NOT NULL | 关系可信度（HIGH/MEDIUM/LOW） |
| data_source | VARCHAR(100) | NOT NULL | 数据来源 |
| verified_at | TIMESTAMP | NULL | 最后验证时间 |
| verified_by | UUID | NULL | 验证者（FK to users） |
| deleted_at | TIMESTAMP | NULL | 软删除时间 |
| deleted_by | UUID | NULL | 软删除操作者 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |
| created_by | UUID | NULL | 创建者（FK to users） |

**索引**：
- `idx_relationships_source ON (source_object_id, relation_type_id) WHERE deleted_at IS NULL`
- `idx_relationships_target ON (target_object_id) WHERE deleted_at IS NULL`
- `idx_relationships_type ON (relation_type_id, status) WHERE deleted_at IS NULL`

### 3.5 relationship_types 表

关系类型定义表，约束允许的源/目标对象类型。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 类型唯一标识 |
| name | VARCHAR(100) | NOT NULL, UNIQUE | 关系类型名称（如contains/installed_in） |
| description | TEXT | NULL | 关系说明 |
| is_directed | BOOLEAN | NOT NULL, DEFAULT TRUE | 是否有方向性 |
| allowed_source_types | JSONB | NULL | 允许的源对象类型数组（如["RACK", "SERVER"]） |
| allowed_target_types | JSONB | NULL | 允许的目标对象类型数组 |
| attributes_schema | JSONB | NULL | 关系属性的 JSON Schema |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**初始数据示例**：

| name | is_directed | allowed_source_types | allowed_target_types | attributes_schema |
| --- | --- | --- | --- | --- |
| contains | TRUE | ["RACK", "SERVER", "GB300_RACK"] | ["SERVER", "GPU", "TRAY"] | {} |
| installed_in | TRUE | ["SERVER", "GPU"] | ["RACK", "TRAY"] | {} |
| connected_to | TRUE | ["NIC", "PORT"] | ["SWITCH", "PORT"] | {"Speed": "string", "Protocol": "string"} |
| feeds | TRUE | ["CDU"] | ["RACK", "SERVER"] | {"FlowRate": "number", "Temperature": "number"} |
| powered_by | TRUE | ["SERVER", "GPU"] | ["POWER_SHELF", "PDU"] | {} |
| depends_on | TRUE | ["SERVER"] | ["SWITCH", "CDU"] | {} |

### 3.6 object_history 表

对象变更历史表，记录所有重要变更。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 历史记录唯一标识 |
| object_id | UUID | FK, NOT NULL | 关联对象（FK to objects） |
| change_type | VARCHAR(100) | NOT NULL | 变更类型（CREATE/UPDATE/DELETE/STATUS_CHANGE/LOCATION_CHANGE） |
| before_data | JSONB | NULL | 变更前数据快照 |
| after_data | JSONB | NULL | 变更后数据快照 |
| source | VARCHAR(100) | NOT NULL | 变更来源（DISCOVERY/MANUAL/IMPORT/API） |
| confidence | VARCHAR(50) | NULL | 变更数据可信度 |
| operator | UUID | NULL | 操作者（FK to users） |
| deleted_at | TIMESTAMP | NULL | 软删除时间 |
| deleted_by | UUID | NULL | 软删除操作者 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**索引**：
- `idx_object_history_object ON (object_id, created_at DESC)`
- `idx_object_history_time ON (created_at) WHERE deleted_at IS NULL`

**分区建议**：按 created_at 月度分区（见 1.4 节）

---

## 4. 业务表 - 资产管理

### 4.1 assets 表

资产记录表，记录设备的商业属性和生命周期。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 资产记录唯一标识 |
| object_id | UUID | FK, NOT NULL, UNIQUE | 关联对象（FK to objects，一对一关系） |
| asset_number | VARCHAR(255) | NOT NULL, UNIQUE | 资产编号（企业内部） |
| lifecycle_status | VARCHAR(50) | NOT NULL | 资产业务状态（枚举见2.2） |
| purchase_request_id | UUID | FK, NULL | 关联采购申请（FK to purchase_requests） |
| purchase_order_id | UUID | FK, NULL | 关联采购订单（FK to purchase_orders） |
| purchase_date | DATE | NULL | 采购日期 |
| received_date | DATE | NULL | 到货日期 |
| vendor | VARCHAR(255) | NULL | 供应商 |
| contract_number | VARCHAR(255) | NULL | 合同编号 |
| warranty_start_date | DATE | NULL | 保修开始日期 |
| warranty_end_date | DATE | NULL | 保修结束日期 |
| warranty_provider | VARCHAR(255) | NULL | 保修提供商 |
| service_level | VARCHAR(100) | NULL | 服务等级（如Gold/Silver） |
| cost | DECIMAL(15,2) | NULL | 采购成本 |
| currency | VARCHAR(10) | NULL | 货币类型（如CNY/USD） |
| version | INT | NOT NULL, DEFAULT 1 | 乐观锁版本号 |
| deleted_at | TIMESTAMP | NULL | 软删除时间 |
| deleted_by | UUID | NULL | 软删除操作者 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |
| created_by | UUID | NULL | 创建者（FK to users） |
| updated_by | UUID | NULL | 更新者（FK to users） |

**索引**：
- `idx_assets_object ON (object_id) WHERE deleted_at IS NULL`
- `idx_assets_status ON (lifecycle_status) WHERE deleted_at IS NULL`
- `idx_assets_vendor ON (vendor) WHERE deleted_at IS NULL`
- `idx_assets_warranty ON (warranty_end_date) WHERE deleted_at IS NULL`

### 4.2 purchase_requests 表

采购申请表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 申请唯一标识 |
| request_number | VARCHAR(100) | NOT NULL, UNIQUE | 申请编号 |
| title | VARCHAR(255) | NOT NULL | 申请标题 |
| object_type_id | UUID | FK, NOT NULL | 申请设备类型（FK to object_types） |
| model | VARCHAR(255) | NULL | 申请型号 |
| quantity | INT | NOT NULL | 申请数量 |
| estimated_cost | DECIMAL(15,2) | NULL | 预计成本 |
| currency | VARCHAR(10) | NULL | 货币类型 |
| justification | TEXT | NULL | 申请理由 |
| preferred_vendor | VARCHAR(255) | NULL | 首选供应商 |
| status | VARCHAR(50) | NOT NULL | 申请状态（DRAFT/PENDING/APPROVED/REJECTED/CANCELLED） |
| workflow_instance_id | UUID | FK, NULL | 关联审批流程（FK to workflow_instance） |
| requester_id | UUID | FK, NOT NULL | 申请人（FK to users） |
| approved_by | UUID | FK, NULL | 批准人（FK to users） |
| approved_at | TIMESTAMP | NULL | 批准时间 |
| rejected_by | UUID | FK, NULL | 拒绝人（FK to users） |
| rejected_at | TIMESTAMP | NULL | 拒绝时间 |
| rejection_reason | TEXT | NULL | 拒绝原因 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引**：
- `idx_purchase_requests_requester ON (requester_id, status)`
- `idx_purchase_requests_status ON (status, created_at DESC)`

### 4.3 purchase_orders 表

采购订单表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 订单唯一标识 |
| order_number | VARCHAR(100) | NOT NULL, UNIQUE | 订单编号 |
| purchase_request_id | UUID | FK, NULL | 关联采购申请（FK to purchase_requests） |
| vendor | VARCHAR(255) | NOT NULL | 供应商 |
| contract_number | VARCHAR(255) | NULL | 合同编号 |
| total_amount | DECIMAL(15,2) | NOT NULL | 订单总额 |
| currency | VARCHAR(10) | NOT NULL | 货币类型 |
| status | VARCHAR(50) | NOT NULL | 订单状态（CREATED/SENT/CONFIRMED/SHIPPED/RECEIVED/CANCELLED） |
| expected_delivery_date | DATE | NULL | 预计到货日期 |
| actual_delivery_date | DATE | NULL | 实际到货日期 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |
| created_by | UUID | FK, NULL | 创建者（FK to users） |

**索引**：
- `idx_purchase_orders_vendor ON (vendor, status)`
- `idx_purchase_orders_delivery ON (expected_delivery_date) WHERE status != 'RECEIVED'`

### 4.4 inventory_records 表

库存事务表，记录入库/出库流水。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 记录唯一标识 |
| transaction_type | VARCHAR(50) | NOT NULL | 事务类型（IN/OUT/TRANSFER/ADJUSTMENT） |
| asset_id | UUID | FK, NOT NULL | 关联资产（FK to assets） |
| quantity | INT | NOT NULL | 数量（正数入库，负数出库） |
| warehouse_location | VARCHAR(255) | NULL | 仓库位置 |
| related_purchase_order_id | UUID | FK, NULL | 关联采购订单（FK to purchase_orders） |
| related_deployment_id | UUID | FK, NULL | 关联部署记录（FK to deployments） |
| operator_id | UUID | FK, NOT NULL | 操作者（FK to users） |
| notes | TEXT | NULL | 备注 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**索引**：
- `idx_inventory_records_asset ON (asset_id, created_at DESC)`
- `idx_inventory_records_type ON (transaction_type, created_at DESC)`

### 4.5 deployments 表

部署记录表，记录设备部署位置变更。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 部署记录唯一标识 |
| asset_id | UUID | FK, NOT NULL | 关联资产（FK to assets） |
| object_id | UUID | FK, NOT NULL | 关联对象（FK to objects） |
| location_id | UUID | FK, NOT NULL | 部署位置（FK to objects） |
| deployment_type | VARCHAR(50) | NOT NULL | 部署类型（NEW/TRANSFER/REPLACEMENT） |
| status | VARCHAR(50) | NOT NULL | 部署状态（PLANNED/IN_PROGRESS/COMPLETED/FAILED） |
| deployed_by | UUID | FK, NULL | 部署人（FK to users） |
| deployed_at | TIMESTAMP | NULL | 部署完成时间 |
| notes | TEXT | NULL | 备注 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引**：
- `idx_deployments_asset ON (asset_id, deployed_at DESC)`
- `idx_deployments_location ON (location_id) WHERE status = 'COMPLETED'`

---

## 5. 业务表 - 运维管理

### 5.1 work_orders 表

工单表，记录运维任务。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 工单唯一标识 |
| work_order_number | VARCHAR(100) | NOT NULL, UNIQUE | 工单编号 |
| title | VARCHAR(255) | NOT NULL | 工单标题 |
| type | VARCHAR(50) | NOT NULL | 工单类型（FAULT/REPAIR/INSPECTION/CHANGE） |
| priority | VARCHAR(50) | NOT NULL | 优先级（CRITICAL/HIGH/MEDIUM/LOW） |
| status | VARCHAR(50) | NOT NULL | 工单状态（枚举见2.3） |
| related_object_id | UUID | FK, NULL | 关联对象（FK to objects） |
| description | TEXT | NULL | 工单描述 |
| fault_record_id | UUID | FK, NULL | 关联故障记录（FK to fault_records） |
| assigned_to | UUID | FK, NULL | 指派工程师（FK to users） |
| created_by | UUID | FK, NOT NULL | 创建者（FK to users） |
| resolved_by | UUID | FK, NULL | 解决者（FK to users） |
| closed_by | UUID | FK, NULL | 关闭者（FK to users） |
| assigned_at | TIMESTAMP | NULL | 指派时间 |
| resolved_at | TIMESTAMP | NULL | 解决时间 |
| closed_at | TIMESTAMP | NULL | 关闭时间 |
| version | INT | NOT NULL, DEFAULT 1 | 乐观锁版本号 |
| deleted_at | TIMESTAMP | NULL | 软删除时间 |
| deleted_by | UUID | NULL | 软删除操作者 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引**：
- `idx_work_orders_assigned ON (assigned_to, status) WHERE deleted_at IS NULL`
- `idx_work_orders_object ON (related_object_id) WHERE deleted_at IS NULL`
- `idx_work_orders_status ON (status, priority, created_at DESC) WHERE deleted_at IS NULL`

### 5.2 fault_records 表

故障记录表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 故障记录唯一标识 |
| object_id | UUID | FK, NOT NULL | 故障对象（FK to objects） |
| fault_type | VARCHAR(100) | NOT NULL | 故障类型（HARDWARE/SOFTWARE/NETWORK/COOLING/POWER） |
| severity | VARCHAR(50) | NOT NULL | 严重程度（CRITICAL/HIGH/MEDIUM/LOW） |
| description | TEXT | NOT NULL | 故障描述 |
| symptoms | TEXT | NULL | 故障现象 |
| evidence | JSONB | NULL | 证据（日志/截图URL等） |
| source | VARCHAR(100) | NOT NULL | 故障来源（BMC/MONITORING/CUSTOMER/ENGINEER/VENDOR） |
| detected_at | TIMESTAMP | NOT NULL | 检测时间 |
| reported_by | UUID | FK, NULL | 报告人（FK to users） |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引**：
- `idx_fault_records_object ON (object_id, detected_at DESC)`
- `idx_fault_records_severity ON (severity, detected_at DESC)`

### 5.3 repair_records 表

维修记录表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 维修记录唯一标识 |
| work_order_id | UUID | FK, NOT NULL | 关联工单（FK to work_orders） |
| object_id | UUID | FK, NOT NULL | 维修对象（FK to objects） |
| repair_type | VARCHAR(100) | NOT NULL | 维修类型（REPLACEMENT/UPGRADE/ADJUSTMENT/CLEANING） |
| description | TEXT | NOT NULL | 维修内容 |
| parts_used | JSONB | NULL | 使用的备件清单 |
| repair_result | VARCHAR(50) | NOT NULL | 维修结果（SUCCESS/FAILED/PARTIAL） |
| engineer_id | UUID | FK, NOT NULL | 维修工程师（FK to users） |
| started_at | TIMESTAMP | NOT NULL | 开始时间 |
| completed_at | TIMESTAMP | NULL | 完成时间 |
| verification_notes | TEXT | NULL | 验证说明 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引**：
- `idx_repair_records_workorder ON (work_order_id)`
- `idx_repair_records_object ON (object_id, completed_at DESC)`

### 5.4 replacement_events 表

部件更换事件表，记录硬件替换。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 更换事件唯一标识 |
| repair_record_id | UUID | FK, NULL | 关联维修记录（FK to repair_records） |
| old_object_id | UUID | FK, NOT NULL | 旧部件（FK to objects） |
| new_object_id | UUID | FK, NOT NULL | 新部件（FK to objects） |
| replacement_reason | VARCHAR(255) | NOT NULL | 更换原因（FAILURE/UPGRADE/PREVENTIVE） |
| old_object_disposition | VARCHAR(100) | NOT NULL | 旧部件去向（RETIRED/RMA/STOCK/SCRAPPED） |
| engineer_id | UUID | FK, NOT NULL | 更换工程师（FK to users） |
| replaced_at | TIMESTAMP | NOT NULL | 更换时间 |
| notes | TEXT | NULL | 备注 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**索引**：
- `idx_replacement_events_old ON (old_object_id, replaced_at DESC)`
- `idx_replacement_events_new ON (new_object_id)`

---

## 6. 业务表 - 知识管理

### 6.1 knowledge_articles 表

知识文章表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 文章唯一标识 |
| title | VARCHAR(255) | NOT NULL | 文章标题 |
| content | TEXT | NOT NULL | 文章内容 |
| type | VARCHAR(50) | NOT NULL | 文章类型（SOP/TROUBLESHOOTING/FAQ/BEST_PRACTICE） |
| status | VARCHAR(50) | NOT NULL | 文章状态（DRAFT/UNDER_REVIEW/PUBLISHED/ARCHIVED） |
| version | INT | NOT NULL, DEFAULT 1 | 文章版本号 |
| is_latest | BOOLEAN | NOT NULL, DEFAULT TRUE | 是否最新版本 |
| author_id | UUID | FK, NOT NULL | 作者（FK to users） |
| reviewer_id | UUID | FK, NULL | 审核人（FK to users） |
| reviewed_at | TIMESTAMP | NULL | 审核时间 |
| published_at | TIMESTAMP | NULL | 发布时间 |
| archived_at | TIMESTAMP | NULL | 归档时间 |
| tags | JSONB | NULL | 标签数组 |
| deleted_at | TIMESTAMP | NULL | 软删除时间 |
| deleted_by | UUID | NULL | 软删除操作者 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引**：
- `idx_knowledge_articles_status ON (status, published_at DESC) WHERE deleted_at IS NULL`
- `idx_knowledge_articles_type ON (type) WHERE status = 'PUBLISHED' AND deleted_at IS NULL`
- `idx_knowledge_articles_tags ON tags USING GIN`

### 6.2 knowledge_relations 表

知识关联表，关联文章与对象/工单。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 关联记录唯一标识 |
| article_id | UUID | FK, NOT NULL | 关联文章（FK to knowledge_articles） |
| related_type | VARCHAR(50) | NOT NULL | 关联类型（OBJECT/WORK_ORDER/FAULT/REPAIR） |
| related_id | UUID | NOT NULL | 关联对象ID |
| relation_reason | VARCHAR(255) | NULL | 关联原因 |
| created_by | UUID | FK, NULL | 创建者（FK to users） |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**索引**：
- `idx_knowledge_relations_article ON (article_id)`
- `idx_knowledge_relations_related ON (related_type, related_id)`

---

## 7. 业务表 - 工作流

### 7.1 workflow_definition 表

工作流定义表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 定义唯一标识 |
| name | VARCHAR(255) | NOT NULL, UNIQUE | 工作流名称 |
| description | TEXT | NULL | 工作流说明 |
| workflow_type | VARCHAR(100) | NOT NULL | 工作流类型（PURCHASE_APPROVAL/REPAIR_APPROVAL/DEPLOYMENT） |
| definition_data | JSONB | NOT NULL | 工作流定义（节点/边/条件） |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | 是否启用 |
| version | INT | NOT NULL, DEFAULT 1 | 定义版本号 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |
| created_by | UUID | FK, NULL | 创建者（FK to users） |

**索引**：
- `idx_workflow_definition_type ON (workflow_type, is_active)`

### 7.2 workflow_instance 表

工作流实例表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 实例唯一标识 |
| workflow_definition_id | UUID | FK, NOT NULL | 关联工作流定义（FK to workflow_definition） |
| related_type | VARCHAR(50) | NOT NULL | 关联业务类型（PURCHASE_REQUEST/WORK_ORDER） |
| related_id | UUID | NOT NULL | 关联业务对象ID |
| status | VARCHAR(50) | NOT NULL | 实例状态（RUNNING/COMPLETED/FAILED/CANCELLED） |
| current_node | VARCHAR(100) | NULL | 当前节点 |
| context_data | JSONB | NULL | 上下文数据 |
| started_by | UUID | FK, NOT NULL | 发起人（FK to users） |
| started_at | TIMESTAMP | NOT NULL | 开始时间 |
| completed_at | TIMESTAMP | NULL | 完成时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引**：
- `idx_workflow_instance_related ON (related_type, related_id)`
- `idx_workflow_instance_status ON (status, started_at DESC)`

### 7.3 workflow_task 表

工作流任务表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 任务唯一标识 |
| workflow_instance_id | UUID | FK, NOT NULL | 关联工作流实例（FK to workflow_instance） |
| node_name | VARCHAR(100) | NOT NULL | 节点名称 |
| task_type | VARCHAR(50) | NOT NULL | 任务类型（APPROVAL/EXECUTION/NOTIFICATION） |
| assigned_to | UUID | FK, NULL | 指派人（FK to users） |
| status | VARCHAR(50) | NOT NULL | 任务状态（PENDING/COMPLETED/SKIPPED/FAILED） |
| decision | VARCHAR(50) | NULL | 决策（APPROVED/REJECTED） |
| comment | TEXT | NULL | 审批意见 |
| assigned_at | TIMESTAMP | NULL | 指派时间 |
| completed_at | TIMESTAMP | NULL | 完成时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引**：
- `idx_workflow_task_instance ON (workflow_instance_id, created_at)`
- `idx_workflow_task_assigned ON (assigned_to, status) WHERE status = 'PENDING'`

---

## 8. 组织权限表

### 8.1 organizations 表

组织表，支持多组织/多租户。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 组织唯一标识 |
| name | VARCHAR(255) | NOT NULL, UNIQUE | 组织名称 |
| org_type | VARCHAR(50) | NOT NULL | 组织类型（INTERNAL/CUSTOMER/VENDOR） |
| parent_org_id | UUID | FK, NULL | 父组织（FK to organizations） |
| contact_email | VARCHAR(255) | NULL | 联系邮箱 |
| contact_phone | VARCHAR(50) | NULL | 联系电话 |
| address | TEXT | NULL | 地址 |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | 是否启用 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引**：
- `idx_organizations_type ON (org_type, is_active)`
- `idx_organizations_parent ON (parent_org_id)`

### 8.2 users 表

用户表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 用户唯一标识 |
| username | VARCHAR(100) | NOT NULL, UNIQUE | 用户名 |
| email | VARCHAR(255) | NOT NULL, UNIQUE | 邮箱 |
| full_name | VARCHAR(255) | NULL | 全名 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希 |
| organization_id | UUID | FK, NOT NULL | 所属组织（FK to organizations） |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | 是否启用 |
| last_login_at | TIMESTAMP | NULL | 最后登录时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**索引**：
- `idx_users_org ON (organization_id, is_active)`
- `idx_users_email ON (email) WHERE is_active = TRUE`

### 8.3 roles 表

角色表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 角色唯一标识 |
| name | VARCHAR(100) | NOT NULL, UNIQUE | 角色名称 |
| description | TEXT | NULL | 角色说明 |
| organization_id | UUID | FK, NULL | 所属组织（NULL表示全局角色） |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**初始角色示例**：
- SUPER_ADMIN：超级管理员
- ASSET_MANAGER：资产管理员
- OPERATION_ENGINEER：运维工程师
- CUSTOMER_VIEWER：客户查看者
- VENDOR_ENGINEER：供应商工程师

### 8.4 permissions 表

权限表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 权限唯一标识 |
| name | VARCHAR(100) | NOT NULL, UNIQUE | 权限名称 |
| resource_type | VARCHAR(100) | NOT NULL | 资源类型（OBJECT/ASSET/WORK_ORDER/USER） |
| action | VARCHAR(50) | NOT NULL | 操作（VIEW/CREATE/EDIT/DELETE/APPROVE） |
| description | TEXT | NULL | 权限说明 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**索引**：
- `idx_permissions_resource ON (resource_type, action)`

### 8.5 user_roles 表

用户角色关联表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 关联唯一标识 |
| user_id | UUID | FK, NOT NULL | 用户（FK to users） |
| role_id | UUID | FK, NOT NULL | 角色（FK to roles） |
| granted_by | UUID | FK, NULL | 授权人（FK to users） |
| granted_at | TIMESTAMP | NOT NULL | 授权时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**索引**：
- `idx_user_roles_user ON (user_id)`
- `idx_user_roles_role ON (role_id)`
- **唯一约束**：`UNIQUE(user_id, role_id)`

### 8.6 role_permissions 表

角色权限关联表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 关联唯一标识 |
| role_id | UUID | FK, NOT NULL | 角色（FK to roles） |
| permission_id | UUID | FK, NOT NULL | 权限（FK to permissions） |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**索引**：
- `idx_role_permissions_role ON (role_id)`
- **唯一约束**：`UNIQUE(role_id, permission_id)`

### 8.7 audit_logs 表

审计日志表。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 日志唯一标识 |
| user_id | UUID | FK, NULL | 操作用户（FK to users） |
| action | VARCHAR(100) | NOT NULL | 操作类型（CREATE/UPDATE/DELETE/APPROVE/TRANSFER/LOGIN） |
| resource_type | VARCHAR(100) | NOT NULL | 资源类型（OBJECT/ASSET/WORKORDER/USER/ROLE） |
| resource_id | UUID | NULL | 资源ID |
| before_data | JSONB | NULL | 修改前数据快照 |
| after_data | JSONB | NULL | 修改后数据快照 |
| ip_address | VARCHAR(50) | NULL | 客户端IP |
| user_agent | TEXT | NULL | 用户代理 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**索引**：
- `idx_audit_logs_user ON (user_id, created_at DESC)`
- `idx_audit_logs_resource ON (resource_type, resource_id, created_at DESC)`
- `idx_audit_logs_action ON (action, created_at DESC)`
- `idx_audit_logs_time ON (created_at DESC)`

### 8.8 user_resource_grants 表

跨组织授权表，支持显式授权用户访问特定组织或对象集合。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 授权记录唯一标识 |
| user_id | UUID | FK, NOT NULL | 用户（FK to users） |
| grant_type | VARCHAR(50) | NOT NULL | 授权类型（ORGANIZATION/OBJECT_SET） |
| target_org_id | UUID | FK, NULL | 目标组织（FK to organizations） |
| object_filters | JSONB | NULL | 对象过滤条件（如 {"object_type": "GPU", "location": "DC1"}） |
| access_level | VARCHAR(50) | NOT NULL | 访问级别（VIEW/EDIT/MAINTAIN） |
| granted_by | UUID | FK, NOT NULL | 授权人（FK to users） |
| granted_at | TIMESTAMP | NOT NULL | 授权时间 |
| expires_at | TIMESTAMP | NULL | 过期时间（NULL 表示永久） |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**索引**：
- `idx_user_resource_grants_user ON (user_id, grant_type)`
- `idx_user_resource_grants_org ON (target_org_id) WHERE grant_type='ORGANIZATION'`

---

## 9. 采集治理表

### 9.1 agents 表

采集代理表，记录数据采集 Agent 注册信息。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | Agent唯一标识 |
| name | VARCHAR(255) | NOT NULL, UNIQUE | Agent名称 |
| agent_type | VARCHAR(100) | NOT NULL | Agent类型（REDFISH/IPMI/SNMP/SSH/API） |
| target_scope | JSONB | NULL | 目标范围（对象类型/组织/位置过滤） |
| endpoint_url | VARCHAR(500) | NULL | 采集目标地址 |
| credentials | TEXT | NULL | 凭证（加密存储） |
| status | VARCHAR(50) | NOT NULL | Agent状态（ACTIVE/INACTIVE/ERROR） |
| last_heartbeat | TIMESTAMP | NULL | 最后心跳时间 |
| collection_interval | INT | NULL | 采集间隔（秒） |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |
| created_by | UUID | FK, NULL | 创建者（FK to users） |

**索引**：
- `idx_agents_status ON (status, last_heartbeat DESC)`
- `idx_agents_type ON (agent_type)`

### 9.2 collection_jobs 表

采集任务表，记录每次数据采集任务。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 任务唯一标识 |
| agent_id | UUID | FK, NOT NULL | 关联Agent（FK to agents） |
| object_id | UUID | FK, NULL | 目标对象（FK to objects） |
| job_type | VARCHAR(100) | NOT NULL | 任务类型（DISCOVERY/SPEC_UPDATE/STATUS_CHECK） |
| status | VARCHAR(50) | NOT NULL | 任务状态（PENDING/RUNNING/SUCCESS/FAILED） |
| started_at | TIMESTAMP | NULL | 开始时间 |
| completed_at | TIMESTAMP | NULL | 完成时间 |
| duration_ms | INT | NULL | 执行耗时（毫秒） |
| success_count | INT | NOT NULL, DEFAULT 0 | 成功数量 |
| fail_count | INT | NOT NULL, DEFAULT 0 | 失败数量 |
| error_message | TEXT | NULL | 错误信息 |
| result_summary | JSONB | NULL | 结果摘要 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**索引**：
- `idx_collection_jobs_agent ON (agent_id, created_at DESC)`
- `idx_collection_jobs_object ON (object_id, created_at DESC)`
- `idx_collection_jobs_status ON (status, created_at DESC)`

### 9.3 collection_failures 表

采集失败表，记录采集失败详情。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 失败记录唯一标识 |
| collection_job_id | UUID | FK, NOT NULL | 关联采集任务（FK to collection_jobs） |
| object_id | UUID | FK, NULL | 目标对象（FK to objects） |
| error_type | VARCHAR(100) | NOT NULL | 错误类型（NETWORK/AUTH/TIMEOUT/PARSE/UNKNOWN） |
| error_detail | TEXT | NOT NULL | 错误详情 |
| retry_count | INT | NOT NULL, DEFAULT 0 | 重试次数 |
| last_retry_at | TIMESTAMP | NULL | 最后重试时间 |
| resolved | BOOLEAN | NOT NULL, DEFAULT FALSE | 是否已解决 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**索引**：
- `idx_collection_failures_job ON (collection_job_id)`
- `idx_collection_failures_object ON (object_id, resolved)`
- `idx_collection_failures_type ON (error_type, created_at DESC)`

---

## 10. 技术基础表

### 10.1 idempotency_keys 表

幂等性键表，防止 API 重复请求。

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PK | 记录唯一标识 |
| idempotency_key | VARCHAR(255) | NOT NULL, UNIQUE | 幂等性键（客户端提供） |
| endpoint | VARCHAR(500) | NOT NULL | API端点 |
| request_hash | VARCHAR(64) | NOT NULL | 请求体哈希（SHA256） |
| response_status | INT | NOT NULL | 响应状态码 |
| response_body | JSONB | NULL | 响应体 |
| user_id | UUID | FK, NULL | 请求用户（FK to users） |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| expires_at | TIMESTAMP | NOT NULL | 过期时间（24小时后） |

**索引**：
- `idx_idempotency_keys_key ON (idempotency_key)`
- `idx_idempotency_keys_expires ON (expires_at)`

**清理策略**：定时任务清理 `expires_at < NOW()` 的记录

---

## 11. 实现顺序

### Phase 1: Core 基础（P0）

1. object_types, objects, object_specs
2. relationship_types, relationships
3. object_history
4. organizations, users, roles, permissions, user_roles, role_permissions
5. audit_logs, idempotency_keys

### Phase 2: Asset 资产（P1）

1. assets
2. purchase_requests, purchase_orders
3. inventory_records, deployments
4. workflow_definition, workflow_instance, workflow_task

### Phase 3: Operations 运维（P2）

1. work_orders, fault_records
2. repair_records, replacement_events

### Phase 4: Knowledge 知识（P3）

1. knowledge_articles, knowledge_relations

### Phase 5: Data Collection 采集（P2）

1. agents, collection_jobs, collection_failures

---

## 12. Migration 管理

所有数据库结构变更通过 Alembic migration 管理：

```bash
# 创建 migration
alembic revision --autogenerate -m "add objects table"

# 应用 migration
alembic upgrade head

# 回滚 migration
alembic downgrade -1
```

每个 migration 必须包含：
- Up 操作（创建表/字段/索引）
- Down 操作（回滚能力）
- 数据迁移脚本（如果需要）

---

## 附录：表统计

- **Core 核心表**：6 张（objects, object_types, object_specs, relationships, relationship_types, object_history）
- **资产管理表**：5 张（assets, purchase_requests, purchase_orders, inventory_records, deployments）
- **运维管理表**：4 张（work_orders, fault_records, repair_records, replacement_events）
- **知识管理表**：2 张（knowledge_articles, knowledge_relations）
- **工作流表**：3 张（workflow_definition, workflow_instance, workflow_task）
- **组织权限表**：7 张（organizations, users, roles, permissions, user_roles, role_permissions, audit_logs）
- **采集治理表**：3 张（agents, collection_jobs, collection_failures）
- **技术基础表**：1 张（idempotency_keys）

**总计：31 张表**
