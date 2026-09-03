# Atlas MVP 数据库初始化与第一批开发任务

| 项目 | 内容 |
| --- | --- |
| 版本 | v0.2 |
| 状态 | Phase 0+1 启动包 |

## 修订说明

> **阶段定义唯一权威：docs/16-Atlas开发任务拆解与Codex执行计划.md**
> 
> 本文档已从"第一阶段"改为"Phase 0+1 启动包"，对齐统一阶段模型。

本版本变更：

- 文档范围从"第一阶段 Core"改为"Phase 0 工程初始化 + Phase 1 Infrastructure Core + Object Explorer"
- 明确首批 migration 的表范围（Core 域 + 权限域 + 治理域，共 13 张表）
- 补充 Object Explorer 前端页面要求
- 补充验收标准（后端 API + 前端页面 + 数据库）
- 与 docs/11、docs/16 对齐阶段定义

---

## 1. 文档目的

本文档用于指导 Atlas MVP **Phase 0 和 Phase 1** 开发。

**Phase 0 目标**：完成项目初始化（工程骨架、Docker 环境、健康检查）

**Phase 1 目标**：完成 Infrastructure Core 与 Object Explorer（对象模型 CRUD + 前端页面）

## 2. Codex 启动要求

执行任何代码前，必须阅读：

- `AGENTS.md`：理解 Codex 代理职责边界
- `README.md`：理解 Atlas 核心理念
- `docs/10-Atlas系统架构设计.md`：理解技术选型与模块边界
- `docs/12-Atlas数据库模型设计.md`：理解数据库表结构与字段定义
- `docs/16-Atlas开发任务拆解与Codex执行计划.md`：理解阶段任务与验收标准

必须理解：Atlas 的核心不是传统资产系统，而是基础设施数字化模型。

**Phase 0+1 必须遵循**：

- **Object First**：所有设备通过 `objects` 表建模，禁止创建 `gpu_table`、`server_table`
- **Relationship Driven**：设备间关系通过 `relationships` 表建模，支持 contains/installed_in/connected_to/powered_by
- **History Based**：所有变更记录到 `object_history` 表，支持审计与回溯

## 3. Phase 0: 工程初始化

### 3.1 目标

建立项目骨架，确保前后端可启动、数据库可连接、迁移框架可用。

### 3.2 交付物

**仓库结构**：

```text
atlas-platform/
├── backend/          # Python 后端
├── frontend/         # Vue 3 前端
├── database/         # 数据库迁移文件
├── docker/           # Docker 配置
├── docs/             # 设计文档
├── scripts/          # 运维脚本
├── tests/            # 测试代码
├── docker-compose.yml
├── README.md
└── .gitignore
```

**后端脚手架**：

```text
backend/
├── app/
│   ├── main.py           # FastAPI 应用入口
│   ├── config/           # 配置管理
│   │   └── settings.py   # 环境变量、数据库 URL、日志配置
│   ├── database/         # 数据库连接
│   │   └── session.py    # SQLAlchemy engine 和 session
│   ├── models/           # SQLAlchemy 数据模型
│   ├── schemas/          # Pydantic 请求/响应模型
│   ├── api/              # API 路由
│   │   └── v1/
│   ├── services/         # 业务逻辑
│   └── core/             # 核心工具（权限、异常、中间件）
├── alembic/              # Alembic 迁移文件
│   ├── versions/
│   └── env.py
├── alembic.ini
├── requirements.txt
└── Dockerfile
```

**前端脚手架**：

```text
frontend/
├── src/
│   ├── main.ts           # Vue 应用入口
│   ├── App.vue
│   ├── router/           # Vue Router 路由配置
│   │   └── index.ts
│   ├── views/            # 页面组件
│   ├── components/       # 可复用组件
│   ├── api/              # API 请求封装（Axios）
│   └── types/            # TypeScript 类型定义
├── package.json
├── tsconfig.json
├── vite.config.ts
└── Dockerfile
```

**Docker Compose**：

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: atlas
      POSTGRES_USER: atlas
      POSTGRES_PASSWORD: atlas
    ports:
      - "5432:5432"
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

### 3.3 验收标准

- [ ] `docker-compose up` 启动所有服务
- [ ] `curl http://localhost:8000/health` 返回 `{"status":"ok"}`
- [ ] `curl http://localhost:8000/docs` 显示 Swagger UI
- [ ] 前端访问 `http://localhost:3000` 显示欢迎页面
- [ ] Alembic 迁移框架可执行 `alembic upgrade head`

---

## 4. Phase 1: Infrastructure Core + Object Explorer

### 4.1 目标

实现对象模型 CRUD API 与 Object Explorer 前端页面，建立 Atlas 数字化基础设施核心。

完成后，Atlas 应能够描述：

- Data Center
- Room
- Rack
- Server
- GPU
- NIC
- CDU
- Power Shelf

### 4.2 首批数据库迁移（Migration 001）

> **重要**：表结构必须遵循 `docs/12-Atlas数据库模型设计.md` v0.2 的字段定义。

**Migration 文件名**：`001_create_infrastructure_core_tables.py`

**包含表**：

#### 4.2.1 Core 域（6 张表）

**`object_types`**：对象类型定义

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 主键 |
| name | VARCHAR(100) | UNIQUE NOT NULL | 类型名称（如 SERVER、GPU） |
| display_name | VARCHAR(200) | NOT NULL | 显示名称 |
| description | TEXT | NULL | 类型描述 |
| icon | VARCHAR(50) | NULL | 图标名称 |
| schema | JSONB | NULL | 该类型的 spec_data JSON Schema |
| allowed_relationships | JSONB | NULL | 允许的关系类型配置 |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新时间 |

**`objects`**：对象主表

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 主键 |
| object_type_id | UUID | FK NOT NULL | 对象类型 |
| name | VARCHAR(255) | NOT NULL | 对象名称 |
| serial_number | VARCHAR(255) | UNIQUE NULL | 序列号（SN） |
| manufacturer | VARCHAR(200) | NULL | 制造商 |
| model | VARCHAR(200) | NULL | 型号 |
| hardware_generation | VARCHAR(100) | NULL | 硬件代数（如 GB300、Hopper） |
| status | VARCHAR(50) | NOT NULL DEFAULT 'PLANNED' | 技术状态（PLANNED/ACTIVE/INACTIVE/MAINTENANCE/RETIRED） |
| owner_org_id | UUID | FK NULL | 所有者组织 |
| operator_org_id | UUID | FK NULL | 运营者组织 |
| maintainer_org_id | UUID | FK NULL | 维护者组织 |
| location | VARCHAR(500) | NULL | 物理位置（文本描述） |
| tags | JSONB | NULL | 标签（数组） |
| data_source | VARCHAR(50) | NULL | 数据来源（manual/import/agent） |
| confidence | DECIMAL(3,2) | NULL | 数据置信度（0.00~1.00） |
| data_status | VARCHAR(50) | NULL | 数据状态（draft/verified/stale） |
| deleted_at | TIMESTAMP | NULL | 软删除时间 |
| deleted_by | UUID | FK NULL | 软删除操作人 |
| version | INT | NOT NULL DEFAULT 1 | 乐观锁版本号 |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新时间 |
| created_by | UUID | FK NULL | 创建人 |
| updated_by | UUID | FK NULL | 更新人 |

**`object_specs`**：对象规格（JSONB 扩展属性）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 主键 |
| object_id | UUID | FK UNIQUE NOT NULL | 对象 ID（一对一） |
| spec_data | JSONB | NOT NULL DEFAULT '{}' | 规格数据（JSON） |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新时间 |

**`relationship_types`**：关系类型定义

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 主键 |
| name | VARCHAR(100) | UNIQUE NOT NULL | 关系类型名称（如 contains、installed_in） |
| display_name | VARCHAR(200) | NOT NULL | 显示名称 |
| description | TEXT | NULL | 关系描述 |
| is_directed | BOOLEAN | NOT NULL DEFAULT TRUE | 是否有方向 |
| allowed_source_types | JSONB | NULL | 允许的源对象类型（数组） |
| allowed_target_types | JSONB | NULL | 允许的目标对象类型（数组） |
| attributes_schema | JSONB | NULL | 关系属性的 JSON Schema |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新时间 |

**`relationships`**：对象间关系

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 主键 |
| source_object_id | UUID | FK NOT NULL | 源对象 ID |
| relationship_type_id | UUID | FK NOT NULL | 关系类型 |
| target_object_id | UUID | FK NOT NULL | 目标对象 ID |
| attributes | JSONB | NULL | 关系属性（如端口号、连接速率） |
| status | VARCHAR(50) | NOT NULL DEFAULT 'ACTIVE' | 关系状态（ACTIVE/INACTIVE） |
| valid_from | TIMESTAMP | NULL | 生效时间 |
| valid_to | TIMESTAMP | NULL | 失效时间 |
| deleted_at | TIMESTAMP | NULL | 软删除时间 |
| deleted_by | UUID | FK NULL | 软删除操作人 |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新时间 |
| created_by | UUID | FK NULL | 创建人 |
| updated_by | UUID | FK NULL | 更新人 |

**`object_history`**：对象变更历史

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 主键 |
| object_id | UUID | FK NOT NULL | 对象 ID |
| action | VARCHAR(50) | NOT NULL | 操作类型（CREATE/UPDATE/DELETE） |
| before_data | JSONB | NULL | 变更前数据 |
| after_data | JSONB | NULL | 变更后数据 |
| changed_fields | JSONB | NULL | 变更字段列表 |
| operator | UUID | FK NULL | 操作人 |
| operator_name | VARCHAR(200) | NULL | 操作人名称（冗余） |
| operation_context | JSONB | NULL | 操作上下文（IP、User-Agent） |
| data_source | VARCHAR(50) | NULL | 数据来源（manual/import/agent） |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 创建时间 |

**索引**：
- `idx_objects_type_status` ON `objects(object_type_id, status) WHERE deleted_at IS NULL`
- `idx_objects_owner` ON `objects(owner_org_id) WHERE deleted_at IS NULL`
- `idx_objects_serial` ON `objects(serial_number) WHERE deleted_at IS NULL`
- `idx_object_specs_data` ON `object_specs USING GIN (spec_data)`
- `idx_relationships_source` ON `relationships(source_object_id) WHERE deleted_at IS NULL`
- `idx_relationships_target` ON `relationships(target_object_id) WHERE deleted_at IS NULL`
- `idx_object_history_object_time` ON `object_history(object_id, created_at DESC)`

#### 4.2.2 权限域（4 张表）

**`organizations`**：组织/租户

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 主键 |
| name | VARCHAR(200) | UNIQUE NOT NULL | 组织名称 |
| code | VARCHAR(50) | UNIQUE NOT NULL | 组织代码 |
| parent_id | UUID | FK NULL | 父组织 ID |
| deleted_at | TIMESTAMP | NULL | 软删除时间 |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新时间 |

**`users`**：用户表

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 主键 |
| username | VARCHAR(100) | UNIQUE NOT NULL | 用户名 |
| email | VARCHAR(200) | UNIQUE NOT NULL | 邮箱 |
| hashed_password | VARCHAR(255) | NOT NULL | 密码哈希 |
| full_name | VARCHAR(200) | NULL | 姓名 |
| organization_id | UUID | FK NULL | 所属组织 |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | 是否激活 |
| is_superuser | BOOLEAN | NOT NULL DEFAULT FALSE | 是否超级用户 |
| deleted_at | TIMESTAMP | NULL | 软删除时间 |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新时间 |

**`roles`**：角色表

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 主键 |
| name | VARCHAR(100) | UNIQUE NOT NULL | 角色名称 |
| description | TEXT | NULL | 角色描述 |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 更新时间 |

**`permissions`**：权限表

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 主键 |
| resource | VARCHAR(100) | NOT NULL | 资源名称（如 object、asset） |
| action | VARCHAR(50) | NOT NULL | 操作（create/read/update/delete） |
| description | TEXT | NULL | 权限描述 |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 创建时间 |

**关联表**：
- `user_roles`：用户-角色关联（user_id, role_id）
- `role_permissions`：角色-权限关联（role_id, permission_id）

#### 4.2.3 治理域（2 张表）

**`idempotency_keys`**：幂等性保证

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 主键 |
| key | VARCHAR(255) | UNIQUE NOT NULL | 幂等键 |
| request_hash | VARCHAR(64) | NOT NULL | 请求哈希 |
| response_data | JSONB | NULL | 响应数据 |
| status | VARCHAR(50) | NOT NULL | 状态（processing/completed/failed） |
| expires_at | TIMESTAMP | NOT NULL | 过期时间 |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 创建时间 |

**`audit_logs`**：审计日志

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 主键 |
| user_id | UUID | FK NULL | 操作用户 |
| action | VARCHAR(100) | NOT NULL | 操作类型 |
| resource_type | VARCHAR(100) | NOT NULL | 资源类型 |
| resource_id | UUID | NULL | 资源 ID |
| request_data | JSONB | NULL | 请求数据 |
| response_status | INT | NULL | 响应状态码 |
| ip_address | VARCHAR(50) | NULL | 客户端 IP |
| user_agent | TEXT | NULL | User-Agent |
| created_at | TIMESTAMP | NOT NULL DEFAULT NOW() | 创建时间 |

**索引**：
- `idx_audit_logs_user_time` ON `audit_logs(user_id, created_at DESC)`
- `idx_audit_logs_resource` ON `audit_logs(resource_type, resource_id, created_at DESC)`

### 4.3 初始化数据

**Object Types**：

```python
object_types = [
    {'name': 'DATACENTER', 'display_name': '数据中心', 'icon': 'datacenter'},
    {'name': 'ROOM', 'display_name': '机房', 'icon': 'room'},
    {'name': 'RACK', 'display_name': '机柜', 'icon': 'rack'},
    {'name': 'SERVER', 'display_name': '服务器', 'icon': 'server'},
    {'name': 'GPU', 'display_name': 'GPU', 'icon': 'gpu'},
    {'name': 'NIC', 'display_name': '网卡', 'icon': 'nic'},
    {'name': 'STORAGE', 'display_name': '存储', 'icon': 'storage'},
    {'name': 'CDU', 'display_name': 'CDU', 'icon': 'cdu'},
    {'name': 'POWER_SHELF', 'display_name': '电源柜', 'icon': 'power'},
]
```

**Relationship Types**：

```python
relationship_types = [
    {'name': 'contains', 'display_name': '包含', 'is_directed': True},
    {'name': 'installed_in', 'display_name': '安装在', 'is_directed': True},
    {'name': 'connected_to', 'display_name': '连接到', 'is_directed': False},
    {'name': 'feeds', 'display_name': '供电给', 'is_directed': True},
    {'name': 'powered_by', 'display_name': '由...供电', 'is_directed': True},
]
```

**默认组织与用户**：

```python
organizations = [
    {'name': 'Atlas Platform', 'code': 'ATLAS'},
]

users = [
    {'username': 'admin', 'email': 'admin@atlas.local', 'full_name': '系统管理员', 'is_superuser': True},
]
```

### 4.4 后端 API 实现

**必需 API**：

#### Object API

- `POST /api/v1/objects`：创建对象
  - Request Body: `{object_type_id, name, serial_number?, manufacturer?, model?, status?, spec_data?}`
  - Response: `{id, ...fields, created_at}`
  
- `GET /api/v1/objects`：查询对象列表
  - Query Params: `object_type_id?`, `status?`, `name?`, `page?`, `page_size?`
  - Response: `{total, items: [{id, name, object_type, status, ...}]}`
  
- `GET /api/v1/objects/{id}`：获取对象详情
  - Response: `{id, ...fields, object_type: {...}, spec_data: {...}}`
  
- `PUT /api/v1/objects/{id}`：更新对象
  - Request Body: `{name?, manufacturer?, model?, status?, spec_data?}`
  - Response: `{id, ...fields, updated_at}`
  - **必须记录 History**：调用前后对比，写入 `object_history` 表
  
- `DELETE /api/v1/objects/{id}`：软删除对象
  - Response: `{message: "deleted"}`
  - **软删除**：设置 `deleted_at`，不物理删除

- `GET /api/v1/objects/{id}/history`：获取对象历史
  - Response: `{items: [{action, before_data, after_data, operator_name, created_at}]}`

#### Relationship API

- `POST /api/v1/relationships`：创建关系
  - Request Body: `{source_object_id, relationship_type_id, target_object_id, attributes?}`
  - Response: `{id, ...fields, created_at}`
  
- `GET /api/v1/relationships`：查询关系
  - Query Params: `source_object_id?`, `target_object_id?`, `relationship_type_id?`
  - Response: `{items: [{id, source_object, relationship_type, target_object, ...}]}`
  
- `DELETE /api/v1/relationships/{id}`：软删除关系

#### Object Type API

- `GET /api/v1/object-types`：获取对象类型列表
  - Response: `{items: [{id, name, display_name, icon}]}`

#### Relationship Type API

- `GET /api/v1/relationship-types`：获取关系类型列表
  - Response: `{items: [{id, name, display_name, is_directed}]}`

**业务逻辑要求**：

- 所有写操作（POST/PUT/DELETE）必须记录 `audit_logs`
- 对象更新（PUT）必须记录 `object_history`（对比 before/after，写入 changed_fields）
- 软删除必须设置 `deleted_at` 和 `deleted_by`，查询时默认过滤 `WHERE deleted_at IS NULL`
- 并发更新必须使用乐观锁（检查 `version` 字段）

### 4.5 前端页面实现

#### Object Explorer 列表页（`/objects`）

**功能**：

- 展示对象列表（表格）
- 列：Name、Type、Status、Manufacturer、Model、Serial Number、Created At
- 筛选：按对象类型、状态、名称搜索
- 分页：支持翻页
- 操作：点击行跳转到详情页、创建按钮

**技术要求**：

- 使用 Vue 3 Composition API
- 使用 TypeScript
- 使用 Element Plus / Ant Design Vue 组件库（二选一）
- 调用 `GET /api/v1/objects` API

#### Object 详情页（`/objects/:id`）

**功能**：

- Tab 1: 基础信息（Name、Type、Status、Manufacturer、Model、SN、Owner、Location、Tags）
- Tab 2: Specification（渲染 spec_data JSONB，支持 key-value 展示）
- Tab 3: Relationships（关系图，使用 D3.js 或 Cytoscape.js 可视化）
- Tab 4: History（时间线展示变更历史）
- 编辑按钮：弹窗编辑基础信息与 spec_data

**技术要求**：

- 使用 Vue 3 Composition API + TypeScript
- 关系图使用图可视化库（推荐 Cytoscape.js）
- 调用 `GET /api/v1/objects/{id}` 和 `GET /api/v1/objects/{id}/history` API

#### Object 创建/编辑表单

**功能**：

- 选择对象类型（下拉框）
- 填写基础信息（Name、SN、Manufacturer、Model、Status、Location）
- 动态表单：根据对象类型的 `schema` 渲染 spec_data 表单字段（JSON Schema Form）
- 提交：调用 `POST /api/v1/objects` 或 `PUT /api/v1/objects/{id}`

**技术要求**：

- 使用 Vue 3 表单组件
- 支持 JSON Schema 动态表单渲染（可使用 @jsonforms/vue 或手工实现）

### 4.6 测试数据脚本

创建测试数据脚本 `scripts/seed_phase1_data.py`，用于快速生成演示数据。

**测试场景**：模拟一个 AI 训练集群的基础设施

**数据结构**：

```text
DC001 (数据中心)
  └── ROOM001 (机房)
      └── GB300-RACK-001 (机柜)
          ├── TRAY001 (Compute Tray)
          │   ├── GPU001 (B300 GPU)
          │   ├── GPU002 (B300 GPU)
          │   └── NIC001 (BF3 NIC)
          ├── TRAY002 (Compute Tray)
          │   ├── GPU003 (B300 GPU)
          │   ├── GPU004 (B300 GPU)
          │   └── NIC002 (BF3 NIC)
          └── CDU001 (CDU)
```

**对象清单**：

1. **DC001**（数据中心）
   - name: "Beijing DC"
   - location: "北京市海淀区"

2. **ROOM001**（机房）
   - name: "Room A"
   - location: "1F-A"
   - relationship: `ROOM001 installed_in DC001`

3. **GB300-RACK-001**（机柜）
   - name: "GB300 Rack 001"
   - manufacturer: "NVIDIA"
   - model: "GB300"
   - location: "Row 1, Position 1"
   - relationship: `GB300-RACK-001 installed_in ROOM001`

4. **TRAY001, TRAY002**（Compute Tray，类型为 SERVER）
   - manufacturer: "NVIDIA"
   - model: "GB300 Compute Tray"
   - relationship: `TRAY001 installed_in GB300-RACK-001`

5. **GPU001~GPU004**（B300 GPU）
   - manufacturer: "NVIDIA"
   - model: "B300"
   - spec_data:
     ```json
     {
       "memory": "288GB",
       "firmware_version": "97.00.xx",
       "pci_bdf": "41:00.0",
       "cuda_cores": 14592,
       "tensor_cores": 456
     }
     ```
   - relationship: `GPU001 installed_in TRAY001`

6. **NIC001, NIC002**（BF3 网卡）
   - manufacturer: "NVIDIA"
   - model: "BlueField-3"
   - spec_data:
     ```json
     {
       "ports": 2,
       "speed": "400Gbps",
       "firmware_version": "24.xx.xx"
     }
     ```
   - relationship: `NIC001 installed_in TRAY001`

7. **CDU001**（CDU 液冷单元）
   - manufacturer: "Vertiv"
   - model: "CDU-500"
   - spec_data:
     ```json
     {
       "cooling_capacity": "500kW",
       "inlet_temp": "15°C",
       "outlet_temp": "25°C"
     }
     ```
   - relationship: `GB300-RACK-001 powered_by CDU001`

**脚本执行**：

```bash
python scripts/seed_phase1_data.py
```

**预期输出**：

```text
Created 1 datacenter
Created 1 room
Created 1 rack
Created 2 compute trays
Created 4 GPUs
Created 2 NICs
Created 1 CDU
Created 10 relationships
Seed data completed!
```

## 5. Phase 1 验收标准

### 5.1 后端验收

- [ ] Backend 可以启动：`uvicorn app.main:app`
- [ ] 访问 `/docs` 可以看到 Swagger API 文档
- [ ] 所有 API 可调用（返回 200 或符合预期的状态码）
- [ ] 数据库包含 13 张表（Core 6 + 权限 4 + 治理 2 + 关联表 1）
- [ ] 执行测试数据脚本后，可通过 SQL 查询到对象与关系

### 5.2 数据库验收

可以查询以下核心数据：

```sql
-- 查询所有对象
SELECT o.name, ot.display_name as type, o.status 
FROM objects o 
JOIN object_types ot ON o.object_type_id = ot.id 
WHERE o.deleted_at IS NULL;

-- 查询 GPU 规格
SELECT o.name, os.spec_data->>'memory' as memory, os.spec_data->>'firmware_version' as firmware
FROM objects o
JOIN object_specs os ON o.id = os.object_id
JOIN object_types ot ON o.object_type_id = ot.id
WHERE ot.name = 'GPU' AND o.deleted_at IS NULL;

-- 查询关系
SELECT so.name as source, rt.display_name as relationship, to.name as target
FROM relationships r
JOIN objects so ON r.source_object_id = so.id
JOIN objects to ON r.target_object_id = to.id
JOIN relationship_types rt ON r.relationship_type_id = rt.id
WHERE r.deleted_at IS NULL;

-- 查询对象历史
SELECT o.name, h.action, h.operator_name, h.created_at
FROM object_history h
JOIN objects o ON h.object_id = o.id
ORDER BY h.created_at DESC;
```

### 5.3 前端验收

- [ ] 访问 `http://localhost:3000/objects` 显示 Object Explorer 列表页
- [ ] 列表页能看到测试数据（10+ 个对象）
- [ ] 可以按对象类型筛选（选择 GPU，只显示 4 个 GPU）
- [ ] 点击对象进入详情页
- [ ] 详情页 Tab 1 显示基础信息（Name、Type、Status、Manufacturer、Model、SN）
- [ ] 详情页 Tab 2 显示 Specification（GPU 的 memory、firmware_version、pci_bdf）
- [ ] 详情页 Tab 3 显示 Relationships（关系图可视化：GPU → Tray → Rack → Room → DC）
- [ ] 详情页 Tab 4 显示 History（创建记录）
- [ ] 可以通过表单创建新对象（创建 GPU005）
- [ ] 可以编辑对象（修改 GPU001 的 firmware_version）
- [ ] 编辑后，History Tab 显示变更记录（before: "97.00.xx", after: "97.01.xx"）

### 5.4 端到端验收

**验收操作流程**：

1. 启动服务：`docker-compose up`
2. 执行数据库迁移：`alembic upgrade head`
3. 执行测试数据脚本：`python scripts/seed_phase1_data.py`
4. 访问前端：`http://localhost:3000/objects`
5. 查看对象列表：验证 10+ 个对象
6. 点击 GPU001：进入详情页
7. 查看 Specification：验证 memory="288GB", firmware_version="97.00.xx"
8. 查看 Relationships：验证关系图显示 GPU001 → TRAY001 → GB300-RACK-001
9. 点击编辑：修改 firmware_version 为 "97.01.xx"
10. 保存后刷新：验证 Specification 已更新
11. 查看 History：验证记录了变更（before/after）
12. 创建新对象：创建 GPU005，manufacturer="NVIDIA", model="B300"
13. 返回列表页：验证 GPU005 已出现

**验收通过标准**：以上 13 个步骤全部成功。

## 6. Codex 执行 Prompt

### 6.1 Phase 0 Prompt

```text
你现在负责 Atlas Platform 的 Phase 0: 工程初始化。

请严格遵守 AGENTS.md 与 docs/18。
请先阅读 README.md、docs/10-系统架构设计.md。

任务：
1. 创建仓库目录结构（backend/frontend/database/docker/docs/scripts/tests）
2. 初始化 Python 后端脚手架（FastAPI + SQLAlchemy + Alembic）
3. 初始化 Vue 3 前端脚手架（TypeScript + Vue Router + Axios）
4. 创建 docker-compose.yml（PostgreSQL + Backend + Frontend）
5. 创建健康检查接口 GET /health
6. 验证：docker-compose up 后，curl http://localhost:8000/health 返回 {"status":"ok"}

禁止：
- 不要编写业务代码（对象模型、API 等待 Phase 1）
- 不要创建数据库表（等待 Phase 1 的 Alembic migration）

完成后输出：
- 修改文件清单
- docker-compose 启动截图或日志
- 健康检查接口测试结果
- 下一步计划（Phase 1）
```

### 6.2 Phase 1 Prompt

```text
你现在负责 Atlas Platform 的 Phase 1: Infrastructure Core + Object Explorer。

请先阅读：
- docs/12-Atlas数据库模型设计.md（表结构定义）
- docs/18-Atlas MVP数据库初始化与第一批开发任务.md（本文档）
- docs/02-基础设施对象模型.md（对象模型理念）

任务：
1. 创建 Alembic migration 001：13 张表（Core 6 + 权限 4 + 治理 2 + 关联表 1）
2. 实现 Object/Relationship 数据模型（SQLAlchemy models）
3. 实现 Object/Relationship API（参考 docs/18 第 4.4 节）
4. 初始化数据（Object Types、Relationship Types、默认组织与用户）
5. 创建测试数据脚本（scripts/seed_phase1_data.py）
6. 实现 Object Explorer 前端页面（列表页、详情页、创建/编辑表单）

关键要求：
- 所有设备必须通过 objects 表建模，禁止创建 gpu_table、server_table
- 对象更新必须记录 object_history（对比 before/after）
- 软删除必须设置 deleted_at，查询时过滤 WHERE deleted_at IS NULL
- 前端详情页必须包含 4 个 Tab：基础信息、Specification、Relationships、History

验收标准：
- 执行 alembic upgrade head 成功
- 执行 python scripts/seed_phase1_data.py 成功
- 访问 http://localhost:3000/objects 显示对象列表
- 点击 GPU001 查看详情，能看到规格、关系图、历史记录
- 编辑 GPU001 后，History Tab 显示变更记录

完成后输出：
- 修改文件清单（models/api/schemas/services/views）
- 数据库迁移文件路径
- API 列表（Swagger 文档截图）
- 前端页面截图（列表页、详情页、关系图）
- 端到端验收结果
```

## 7. 开发纪律

每完成一个子任务，必须提交 Git commit。

**Phase 0 示例**：

```bash
git commit -m "chore: initialize project structure"
git commit -m "feat(docker): add docker-compose configuration"
git commit -m "feat(api): add health check endpoint"
```

**Phase 1 示例**：

```bash
git commit -m "feat(db): add migration 001 for infrastructure core tables"
git commit -m "feat(core): implement object and relationship models"
git commit -m "feat(api): implement object CRUD API"
git commit -m "feat(api): implement relationship API"
git commit -m "feat(ui): implement Object Explorer list page"
git commit -m "feat(ui): implement Object detail page with tabs"
git commit -m "chore: add seed data script for phase 1"
```

提交前应确认：

- 代码通过 linter 检查（Python: black/flake8, TypeScript: eslint/prettier）
- 数据库迁移可执行（`alembic upgrade head` 和 `alembic downgrade -1` 无错误）
- API 可访问（Swagger 文档无报错）
- 前端页面无明显 bug（控制台无 Error）
- 文档已同步更新

## 8. 后续阶段

完成 Phase 0+1 后，依次进入：

1. **Phase 2: 数据接入层**（Excel/CSV 导入）
2. **Phase 3: Asset Management**（采购、库存、部署）
3. **Phase 4: Operations Management**（工单、故障、维修）
4. **Phase 5: Dashboard 与 Knowledge**（综合视图、文档管理）
5. **Phase 6: Agent 采集**（自动化数据采集，可选）

详见 `docs/16-Atlas开发任务拆解与Codex执行计划.md`。

## 9. 阶段总结

Phase 0+1 的目标不是完成 Atlas 全部功能，而是建立：

```text
Atlas Digital Infrastructure Core
```

这是未来以下能力的基础：

- 资产管理（Asset Management）
- 运维管理（Operations Management）
- 知识管理（Knowledge Management）
- AI 助手（RAG + LLM）
- 自动化能力（Agent 采集 + Workflow）

**核心价值**：

- **Object First**：统一对象模型，避免为每种设备创建独立表
- **Relationship Driven**：通过关系描述基础设施拓扑，支持复杂查询
- **History Based**：记录所有变更，支持审计与回溯
- **Extensible**：通过 JSONB spec_data 支持任意设备类型的扩展属性

完成 Phase 0+1 后，Atlas 已具备描述 AI 基础设施数字化模型的核心能力。

