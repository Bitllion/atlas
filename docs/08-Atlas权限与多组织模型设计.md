# Atlas 权限与多组织模型设计

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | 平台能力设计文档 |

## 1. 目标

支持企业内部、客户环境、供应商、多数据中心、多项目和多组织场景，确保用户只能访问和操作授权范围内的资源。

## 2. 组织、用户和角色

```text
Organization → User → Role → Permission
```

组织可以是 Atlas 企业、客户或供应商。资源分别表达 Owner、Operator、Maintainer 和 Viewer。

角色示例：Asset Manager、Operation Engineer、Customer Viewer、Vendor Engineer。

## 3. 权限与资源范围

```text
User → Role → Permission → Resource Scope → Management Scope
```

操作可包括 VIEW、EDIT、DELETE、MAINTAIN 和 TRANSFER。用户可能只能访问 Customer A 的 GB300，不能访问 Customer B。

## 4. 管理范围

资产属于 Atlas 公司但部署在客户环境时，可能只有 Hardware Maintenance Only 权限：可查看资产、创建维修记录和更新硬件状态，但不能登录系统、修改 OS 或执行命令。

供应商只能访问指定设备和故障信息，不能查看商业资产信息或其他客户资源。

## 5. 审计与 MVP

敏感操作必须记录用户、时间、操作、对象、修改前和修改后数据。第一阶段实现用户、角色、基础权限和数据范围；后续实现多组织、客户隔离、供应商访问和细粒度资源策略。
