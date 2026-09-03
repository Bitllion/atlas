# Atlas 前端设计规范

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | 前端架构设计文档 |

## 1. 目标

让用户以基础设施对象为中心管理 AI 基础设施。设备详情应同时展示它是什么、属于哪里、连接什么、当前状态、历史、资产、运维和知识。

## 2. 技术与导航

Vue 3、TypeScript、Vite、Element Plus、ECharts。导航包括 Dashboard、Infrastructure、Asset、Operations、Knowledge 和 Administration。

## 3. 页面

- Dashboard：资产数量、对象状态、数据质量和最近事件
- Infrastructure：Object、Topology、Location
- Object Detail：Basic Info、Specification、Relationship Graph、Asset、Operations History、Knowledge、Audit History
- Asset：Purchase、Inventory、Deployment、Lifecycle
- Operations：Work Order、Fault、Repair、Inspection
- Knowledge：Documents、SOP、Cases

## 4. 交互原则

列表默认展示 Object Name、Type、Status、Location、Owner、Last Update，支持按 Type、Manufacturer、Location、Status 和 Customer 过滤。高级规格展开显示，并清晰展示来源、更新时间和可信度。

权限决定可见资源和操作，不制作孤立的 GPU 或 Server 页面。
