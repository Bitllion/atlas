# Atlas 数据库模型设计

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | 数据库设计文档 |

数据库使用 PostgreSQL，模型围绕 Object Core 构建，不创建 `servers`、`gpus`、`nics` 等传统硬件专用核心表。

## 1. Core 表

- `objects`：id、object_type_id、name、serial_number、asset_number、manufacturer、model、status、ownership、created_at、updated_at
- `object_types`：id、name、category、description、schema
- `object_specs`：id、object_id、spec_data（JSONB）、version、created_at
- `relationships`：id、source_object_id、relation_type_id、target_object_id、attributes、status、created_at
- `relationship_types`：id、name、description；第一阶段包括 contains、installed_in、connected_to、feeds、powered_by
- `object_history`：id、object_id、change_type、before_data、after_data、source、operator、created_at

## 2. 业务表

- `assets`：object、资产编号、采购日期、供应商、维保、所有组织和状态
- `purchase_requests`、`purchase_orders`
- `inventory_records`、`deployments`
- `work_orders`、`fault_records`、`repair_records`、`replacement_events`
- `knowledge_articles`、`knowledge_relations`
- `workflow_definition`、`workflow_instance`、`workflow_task`
- `users`、`roles`、`permissions`、`audit_logs`

## 3. 规则

对象和关系禁止物理删除，使用 retired 或 inactive 并保留历史。JSONB 只放硬件差异属性，核心查询字段必须结构化。所有结构变更通过 Alembic migration 管理。

## 4. 实现顺序

Core → Asset → Operations → Knowledge；每阶段保持模型、迁移、API 和测试一致。
