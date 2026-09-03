# Atlas MVP 版本开发规划

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.1 |
| 状态 | 开发规划文档 |

## 1. 总体目标

> 建立 AI 基础设施资源数字化管理平台，实现设备对象建模、资产管理以及基础运营能力。

一期重点是模型正确、数据可管理、业务可运行；暂不重点实现自动化、实时监控、AI 助手和复杂流程。

## 2. 优先级

```text
P0 Infrastructure Core
P1 Asset Management
P2 Basic Operations
P3 Knowledge
P4 Automation
```

## 3. 分阶段范围

- P0：Object、ObjectType、Specification、Relationship、History；支持 Data Center、Room、Rack、Server、GPU、NIC、Storage、CDU、Power Shelf。
- P1：采购申请、验收、入库、出库、部署和生命周期。
- P2：工单、故障、维修和基础状态流转。
- P3：文档上传、分类和对象关联。
- P4：只预留 Agent、Redfish、IPMI、SNMP、PXE 和验证接口，不实现自动修复和 Firmware 自动升级。

## 4. 页面与验收

页面包括 Dashboard、CMDB、Asset、Operations 和 Knowledge。MVP 必须能创建 GB300 Rack、Compute Tray、GPU、BF3 NIC，建立关系，管理采购、入库、部署和维修，并查看完整生命周期。

## 5. 路线

工程初始化 → Core → Asset → Operations → Dashboard / 搜索 / 导入导出 → Agent → Knowledge AI → Automation。
