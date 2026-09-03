# Atlas 知识管理与 AI 能力设计

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | 业务设计文档 |

## 1. 定位

Knowledge Domain 不是孤立的文档管理系统，而是将基础设施知识与 Object、Relationship、History 和 Operations 关联，形成面向 AI 基础设施的知识体系。

## 2. 知识类型

- 产品知识：Datasheet、白皮书、产品手册
- 运维 SOP：GPU 更换、服务器验收、Firmware 升级、液冷巡检
- 故障知识：现象、原因、处理方法、验证结果
- 项目经验：客户部署、机房改造和设备交付经验
- 资产技术档案：采购、验收、部署、维修和变更资料

## 3. 关联模型

```text
Knowledge → Infrastructure Object
         → History
         → Operations Record
         → Specification / Firmware
         → Customer / Site
```

例如 B300 Firmware Upgrade Guide 可关联 GPU:B300、Firmware 版本、历史升级记录和维修案例。

## 4. AI Assistant 场景

- 设备助手：结合 Object、Specification、History 回答设备状态
- 故障助手：结合 Fault Record、知识文章和历史案例分析故障
- 运维助手：返回 SOP、注意事项和工具要求

知识检索必须使用对象上下文，同时考虑型号、当前 Firmware、历史故障和客户环境。

## 5. 生命周期与质量

### 5.1 状态流转

```text
DRAFT → UNDER_REVIEW → PUBLISHED → ARCHIVED
  ↑         ↓               ↓
  └─────────┴───────────────┘ (可退回修改或归档)
```

### 5.2 状态字段设计

基于 `docs/12-Atlas数据库模型设计.md` 的 `knowledge_articles` 表定义：

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| **status** | VARCHAR(50) | NOT NULL | 文章状态（枚举值见下表） |
| **version** | INT | NOT NULL, DEFAULT 1 | 文章版本号（每次修改递增） |
| **is_latest** | BOOLEAN | NOT NULL, DEFAULT TRUE | 是否为最新版本（支持版本历史查询） |
| **author_id** | UUID | FK, NOT NULL | 作者（FK to users） |
| **reviewer_id** | UUID | FK, NULL | 审核人（FK to users） |
| **reviewed_at** | TIMESTAMP | NULL | 审核时间 |
| **published_at** | TIMESTAMP | NULL | 发布时间 |
| **archived_at** | TIMESTAMP | NULL | 归档时间 |

**状态枚举定义**：

| 状态 | 说明 | 允许操作 |
| --- | --- | --- |
| **DRAFT** | 草稿 | 编辑、提交审核、删除 |
| **UNDER_REVIEW** | 审核中 | 审核通过、审核拒绝（退回 DRAFT） |
| **PUBLISHED** | 已发布 | 归档、创建新版本（生成新 DRAFT） |
| **ARCHIVED** | 已归档 | 恢复发布（状态回到 PUBLISHED） |

**状态转换规则**：

- `DRAFT → UNDER_REVIEW`：作者提交审核，设置 `reviewer_id`
- `UNDER_REVIEW → PUBLISHED`：审核通过，设置 `reviewed_at` 和 `published_at`
- `UNDER_REVIEW → DRAFT`：审核拒绝，清空 `reviewer_id` 和 `reviewed_at`
- `PUBLISHED → ARCHIVED`：手动归档，设置 `archived_at`
- `PUBLISHED → DRAFT`：创建新版本，旧版本 `is_latest = FALSE`，新版本 `version = version + 1`

### 5.3 数据治理

记录来源、作者、创建时间、更新时间、适用范围、版本和可信度。运维关闭后，应支持将 Work Order 转换为 Solution，再沉淀为 Knowledge Article。

## 6. MVP

- 文档管理
- 分类管理
- 对象关联
- 运维记录关联

全文搜索、标签、推荐、AI Assistant 和 RAG 作为后续阶段。
