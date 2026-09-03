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

```text
创建 → 审核 → 发布 → 使用 → 更新 → 归档
```

记录来源、作者、创建时间、更新时间、适用范围、版本和可信度。运维关闭后，应支持将 Work Order 转换为 Solution，再沉淀为 Knowledge Article。

## 6. MVP

- 文档管理
- 分类管理
- 对象关联
- 运维记录关联

全文搜索、标签、推荐、AI Assistant 和 RAG 作为后续阶段。
