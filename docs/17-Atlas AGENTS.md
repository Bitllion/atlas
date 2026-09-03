# Atlas AGENTS.md 设计说明

## 1. 文件职责

`README.md` 介绍 Atlas；`docs/*.md` 描述设计方案；根目录 `AGENTS.md` 约束 Codex 的开发行为。本文件记录 AGENTS.md 的设计原则和内容结构。

## 2. Codex 首要约束

开发前必须阅读 README、产品定义、业务架构、对象模型、关系模型、系统架构、MVP 规划和工程结构文档；涉及具体模块时还必须阅读对应设计文档。

## 3. 核心原则

- Object First：所有基础设施实体统一为 Object。
- Relationship Driven：设备连接通过 Relationship 表达。
- Asset 与 Object 分离。
- 数据来源透明，记录 Source、Timestamp、Operator 和 Confidence。
- 历史不可覆盖。
- MVP 使用模块化单体和独立 Agent。
- 不默认设备可访问、可实时采集或可自动控制。

## 4. 禁止事项

禁止绕过 Object 模型、创建重复硬件核心表、将核心字段塞入 JSON、提前微服务化、忽略客户环境限制，以及未经设计删除模型、改变数据含义或实现未来自动化功能。

## 5. 开发闭环

```text
阅读文档 → 检查模型 → 确认 API / 页面 → 编码 → 测试 → 同步文档 → 提交
```

完成任务必须说明修改内容、文件、数据库变化、API 变化和测试结果。
