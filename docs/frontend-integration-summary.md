# 前端整合完成总结

## 任务概述
在 `frontend-integration` 分支完成了所有后端功能的前端整合，包括通知系统、工作流审批、数据质量中心和知识 AI 问答。

## 完成的功能

### 1. 通知铃铛 (App.vue)
**位置**: App.vue 顶部栏

**功能**:
- 通知铃铛图标，显示未读消息红点徽章
- 每 30 秒轮询 `/notifications/my/unread-count` 更新未读数
- 点击铃铛显示下拉通知列表（最近 10 条）
- 通知类型图标：📋 工作流任务，📢 其他通知
- 点击通知标记为已读并跳转到相关实体：
  - `WORK_ORDER` → `/work-orders/{id}`
  - `PURCHASE_REQUEST` → `/purchase-requests`
- "全部已读"按钮调用 `PUT /notifications/read-all`

**API 集成**:
- `GET /notifications/my` - 分页获取通知列表
- `GET /notifications/my/unread-count` - 获取未读数
- `PUT /notifications/{id}/read` - 标记单条已读
- `PUT /notifications/read-all` - 全部标记已读

### 2. 我的审批 (ApprovalsView)
**路由**: `/approvals`

**功能**:
- 侧栏菜单项"我的审批"（仅当用户有角色时显示）
- 显示当前用户的待审批任务列表（`status === 'PENDING'`）
- 任务信息：任务 ID、流程实例 ID、节点 ID、创建时间
- 批准/驳回操作：
  - 弹出模态框输入审批意见（可选）
  - 调用 `POST /workflow/tasks/{id}/approve` 或 `reject`
- 操作完成后自动刷新列表

**API 集成**:
- `GET /workflow/tasks/my` - 获取我的待办任务
- `POST /workflow/tasks/{id}/approve` - 批准任务
- `POST /workflow/tasks/{id}/reject` - 驳回任务

### 3. 采购申请工作流状态 (PurchaseRequestsView)
**路由**: `/purchase-requests`

**增强功能**:
- 列表新增"工作流"列，显示工作流状态：
  - 若实例状态为 `RUNNING`，显示"审批中 (节点名称)"
  - 否则显示"—"
- 操作逻辑更新：
  - 仅在 `status === 'PENDING'` 且无活跃工作流时显示旧的批准/驳回按钮
  - 有活跃工作流（`RUNNING`）时隐藏操作按钮，避免冲突

**API 集成**:
- `GET /purchase-requests/{id}/workflow` - 获取采购申请的工作流实例
- 后端已实现 409 冲突检测，前端提前判断避免调用

### 4. 数据质量中心 (QualityView)
**路由**: `/quality`

**功能**:
- 侧栏新增"数据质量"菜单项（在"数据质量"分组下）
- 三个标签页：

#### 4.1 质量概览
- 按对象类型汇总数据质量指标：
  - 总数、缺 SN、缺厂商、缺型号、缺规格
  - STALE/UNKNOWN 状态数量、低置信度数量
- 表格展示，一目了然查看各类型数据完整性

#### 4.2 问题明细
- 筛选器：按对象类型、缺失字段筛选
- 缺失字段选项：缺 SN、缺厂商、缺型号、缺规格
- 列表显示：对象名称、类型、缺失字段、数据状态、置信度
- 支持分页

#### 4.3 未归属对象
- 列出 `owner_org_id` 和 `operator_org_id` 都为空的对象
- 显示：对象名称、类型、序列号、厂商、型号、状态
- 支持分页

**API 集成**:
- `GET /quality/overview` - 质量概览汇总
- `GET /quality/details?type=&missing=&page=&page_size=` - 问题明细
- `GET /quality/unattributed?page=&page_size=` - 未归属对象

### 5. 知识 AI 问答 (KnowledgeListView)
**路由**: `/knowledge`

**增强功能**:
- 知识库列表页顶部新增"💬 AI 问答"区域
- 提问表单：
  - 文本框输入问题
  - "提问"按钮触发 AI 查询
- 响应显示：
  - **未配置 LLM**: 显示警告"⚠️ LLM 未配置"，仅显示参考来源
  - **已配置 LLM**: 显示 AI 回答（带来源标注）+ 参考来源列表
  - **参考来源**: 可点击跳转到对应知识文章详情页
- 搜索结果包含：文章标题、类型、摘要

**API 集成**:
- `POST /knowledge/ask` - AI 问答
  - 请求: `{ question: string }`
  - 响应: `{ answer: string|null, configured: boolean, sources: [{id, title, type, summary}] }`

## 技术实现

### 新增文件
```
frontend/src/api/notifications.ts       # 通知 API 客户端
frontend/src/api/workflow.ts            # 工作流 API 客户端
frontend/src/api/quality.ts             # 数据质量 API 客户端
frontend/src/views/ApprovalsView.vue    # 我的审批页面
frontend/src/views/QualityView.vue      # 数据质量中心页面
```

### 修改文件
```
frontend/src/App.vue                    # 添加通知铃铛 + 我的审批入口
frontend/src/router/index.ts            # 新增路由：/approvals, /quality
frontend/src/types/index.ts             # 新增类型定义
frontend/src/api/knowledge.ts           # 添加 ask 方法
frontend/src/api/assets.ts              # 添加 getPurchaseWorkflow 方法
frontend/src/views/KnowledgeListView.vue # 添加 AI 问答区
frontend/src/views/PurchaseRequestsView.vue # 添加工作流状态显示
frontend/src/style.css                  # 新增样式：通知下拉、AI 问答
```

### 类型定义
```typescript
// 通知
interface Notification {
  id: string; recipient_id: string; type: string; title: string; message: string
  entity_type: string | null; entity_id: string | null; is_read: boolean; 
  read_at: string | null; created_at: string
}

// 工作流
type WorkflowStatus = 'RUNNING' | 'COMPLETED' | 'REJECTED' | 'CANCELLED'
type TaskStatus = 'PENDING' | 'APPROVED' | 'REJECTED'
interface WorkflowTask { ... }
interface WorkflowInstance { ... }

// 数据质量
interface QualityOverviewItem { ... }
interface QualityDetailItem { ... }
interface QualityUnattributedItem { ... }
```

## 验证结果

### 后端测试
- ✅ 所有 65 个测试通过
- 包括通知、工作流、数据质量、知识 AI 相关测试

### 前端构建
- ✅ TypeScript 编译成功
- ✅ Vite 打包成功，无错误
- 生成的页面组件：
  - ApprovalsView
  - QualityView
  - KnowledgeListView (增强)
  - PurchaseRequestsView (增强)

## 用户体验要点

1. **通知系统**: 实时提醒（30秒轮询），点击跳转，一键全部已读
2. **工作流审批**: 集中展示待办任务，支持批注审批，操作后即时刷新
3. **数据质量**: 三视图（概览/明细/未归属），按需筛选，分页浏览
4. **AI 问答**: 智能检索知识库，未配置 LLM 时降级到纯搜索模式
5. **采购流程**: 工作流与旧审批流程兼容共存，状态透明可见

## 兼容性说明

- **采购审批**: 新工作流（流程引擎）与旧审批逻辑（直接 approve/reject）兼容
  - 有活跃工作流时，隐藏旧按钮
  - 后端已实现 409 冲突保护
- **知识 AI**: 支持 LLM 未配置场景，降级为纯搜索模式
- **角色权限**: "我的审批"入口仅对有角色的用户显示

## 下一步建议

1. **通知增强**: 考虑 WebSocket 实时推送替代轮询
2. **工作流可视化**: 添加流程图展示当前节点位置
3. **数据质量**: 批量修复工具、质量评分趋势图
4. **AI 问答**: 增加历史记录、收藏功能
5. **采购详情页**: 独立详情页展示完整工作流历史

## 提交信息

分支: `frontend-integration`
基于: `main` (包含工作流/通知/质量中心/AI 问答全部后端)
测试: 65 passed (后端)
构建: ✅ 成功

准备合并到 `main`。
