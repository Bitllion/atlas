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

## 5. 数据冲突处理规则

### 5.1 来源优先级

当同一对象的同一字段存在多个来源的数据时，按以下优先级选择主版本：

1. **Agent 自动采集** > **人工录入** > **文档/厂商资料**
2. **同优先级取最近更新**：同为 Agent 采集时，取 `updated_at` 最新的记录

### 5.2 关键字段冲突不自动覆盖

对于以下关键字段，冲突时不自动覆盖，而是产生冲突告警待人工仲裁：

- **序列号（serial_number）**：不同来源报告不同 SN，可能存在标签错误或设备替换未记录
- **固件版本（firmware_version）**：不同来源报告不同版本，可能存在未记录的升级或采集时间差
- **位置归属（deployed_location_id）**：不同来源报告不同位置，可能存在搬迁未记录

冲突告警记录在 `audit_logs` 表，`action=DATA_CONFLICT`，包含：

```json
{
  "field": "serial_number",
  "existing_value": "SN123456",
  "existing_source": "DISCOVERY",
  "new_value": "SN654321",
  "new_source": "MANUAL",
  "resolution": "PENDING"
}
```

### 5.3 多来源多版本支持

`object_specs` 表支持每来源一条记录（每条记录有 `data_source` 字段），前端按 5.1 优先级规则选主版本展示：

- **查询默认版本**：`SELECT * FROM object_specs WHERE object_id=:id AND deleted_at IS NULL ORDER BY (CASE data_source WHEN 'DISCOVERY' THEN 1 WHEN 'MANUAL' THEN 2 ELSE 3 END), updated_at DESC LIMIT 1`
- **查询所有版本**：供管理员对比和仲裁冲突

---

## 6. 数据时效性分级

### 6.1 采集间隔策略

| 环境类型 | 采集间隔 | data_status 映射 | 说明 |
| --- | --- | --- | --- |
| 自有机房 Agent 实时 | 5 分钟 | 5 分钟内=FRESH, 1 小时内=NORMAL, >1 小时=STALE | BMC/Redfish 自动采集 |
| 客户环境允许 Agent | T+1 每日同步 | 24 小时内=NORMAL, >24 小时=STALE | 每日凌晨批量同步 |
| 客户环境离线 | T+7 人工导入 | 7 天内=NORMAL, >7 天=STALE | Excel/CSV 人工导入 |
| 从未采集 | - | UNKNOWN | 仅从文档创建对象，无实测数据 |
| 采集失败 | - | INVALID | 最近一次采集失败，无可用数据 |

### 6.2 data_status 自动更新逻辑

- **采集成功后**：`data_status=FRESH`, `last_successful_update=NOW()`
- **定时扫描任务**（每 10 分钟执行）：
  - `last_successful_update < NOW() - INTERVAL '5 minutes'` 且 `data_status=FRESH` → 置为 `NORMAL`
  - `last_successful_update < NOW() - INTERVAL '1 hour'` 且 `data_status=NORMAL` → 置为 `STALE`
  - 客户环境对象按 24 小时阈值计算

---

## 7. 关系数据治理

### 7.1 关系可信度计算规则

`relationships` 表的 `confidence` 字段计算规则：

1. **取源与目标对象 confidence 最小值**：关系的可信度不能高于任一端点
   - 源对象 `confidence=HIGH`，目标对象 `confidence=MEDIUM` → 关系 `confidence=MEDIUM`
2. **按来源覆盖**：如果关系本身由 Agent 自动发现（如 LLDP/CDP），取 Agent 的 `confidence`
3. **人工确认提升**：关系经过工程师验证后（`verified_by` 非空），可提升为 `HIGH`

### 7.2 关系失效处理

当关系不再有效时（如网络断连、设备搬迁）：

- **旧记录置 `status=INACTIVE`**（不删除）
- **保留 `verified_at` 作为"当时有效"证据**：支持历史分析和故障排查
- **创建新关系记录**：如果重新连接到不同对象

示例：GPU 从 Server A 搬迁到 Server B：

```sql
-- 旧关系置为 INACTIVE
UPDATE relationships SET status='INACTIVE', updated_at=NOW()
WHERE source_object_id=:gpu_id AND target_object_id=:server_a_id;

-- 创建新关系
INSERT INTO relationships (source_object_id, target_object_id, relation_type_id, status, confidence, data_source, verified_at)
VALUES (:gpu_id, :server_b_id, 'installed_in', 'ACTIVE', 'HIGH', 'MANUAL', NOW());
```

---

## 8. 采集失败处理机制

### 8.1 失败处理流程

1. **保留最后一次成功数据**：`object_specs` 表的 `spec_data` 不覆盖
2. **data_status 置 INVALID**：标记数据不可信
3. **记录失败详情**：在 `collection_failures` 表记录错误类型、详情和重试次数
4. **自动重试**：根据 `error_type` 决定重试策略：
   - `NETWORK/TIMEOUT`：立即重试 3 次（间隔 10s/30s/60s）
   - `AUTH`：不自动重试，需人工修复凭证
   - `PARSE`：记录详情供开发团队修复采集脚本
5. **连续失败告警**：连续失败 N 次（自有机房 N=12 即 1 小时，客户环境 N=3 即 3 天）后，产生告警工单

### 8.2 与 docs/12 三表对齐

- **agents 表**：记录 Agent 注册信息、状态和最后心跳
- **collection_jobs 表**：记录每次采集任务的状态、耗时和成功/失败数量
- **collection_failures 表**：记录失败详情、重试次数和是否已解决

伪代码示例：

```python
def handle_collection_failure(job_id, object_id, error):
    # 1. 记录失败
    failure = insert_collection_failure(job_id, object_id, error)
    
    # 2. 更新 object_specs.data_status
    update_object_specs(object_id, data_status='INVALID')
    
    # 3. 判断是否需要重试
    if error.type in ['NETWORK', 'TIMEOUT'] and failure.retry_count < 3:
        schedule_retry(job_id, delay=10 * (2 ** failure.retry_count))
    
    # 4. 检查连续失败次数
    failures = get_recent_failures(object_id, hours=1)
    if len(failures) >= 12:
        create_alert_work_order(object_id, failures)
```

---

## 9. 客户环境数据回传方案

### 9.1 三种回传方式

| 方式 | 适用场景 | 数据来源标记 | 说明 |
| --- | --- | --- | --- |
| **Agent 边缘部署** | 客户内网允许部署 Agent | DISCOVERY | Agent 定期推送数据到 Atlas 中心 API |
| **离线介质导入** | 客户内网隔离，允许 U 盘 | IMPORT | 导出 JSON/CSV，人工拷贝后导入 |
| **人工 Excel 录入** | 客户不允许任何自动化 | MANUAL | 工程师根据客户提供的截图/文档录入 |

### 9.2 Agent 边缘部署架构

```text
[Customer Internal Network]
  ├─ Atlas Agent (Docker/K8s)
  │   ├─ Redfish Collector
  │   ├─ SNMP Collector
  │   └─ Local Cache (SQLite)
  │
  └─ HTTPS Push (TLS mutual auth)
       ↓
[Atlas Central API]
  └─ /api/v1/collection/batch_import
```

- **Agent 本地缓存**：客户网络不稳定时，数据缓存至本地 SQLite，恢复后推送
- **TLS 双向认证**：Agent 证书由 Atlas 签发，防止伪造数据
- **增量推送**：仅推送变更的 `object_specs` 记录，减少带宽

### 9.3 MVP 优先级

- **MVP 阶段（P0）**：优先支持 **Excel 导入** 和 **人工录入**，覆盖客户环境基础需求
- **增强阶段（P1）**：支持 **Agent 边缘部署**，提升自有机房和允许 Agent 的客户环境自动化水平
- **离线介质导入（P2）**：后续补充，适配高安全隔离客户

---

## 10. 客户环境与 MVP

客户设备可以是 `OWNED`、位于 Customer DC、`NO_DIRECT_ACCESS`，数据来源为 Customer Report。第一阶段支持手工录入、Excel 导入、来源记录和历史；第二阶段支持 Redfish、IPMI、SNMP 和 Agent；第三阶段支持自动发现、质量评分和 AI 数据分析。
