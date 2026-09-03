# API 设计

## 1. 设计原则

API 围绕资源和领域模型设计，不根据页面创建临时接口。

## 2. Object API

```http
POST /api/v1/objects
GET /api/v1/objects
GET /api/v1/objects/{id}
PUT /api/v1/objects/{id}
```

## 3. Relationship API

```http
POST /api/v1/relationships
GET /api/v1/relationships
GET /api/v1/objects/{id}/relations
```

## 4. Specification 与 History API

```http
GET /api/v1/objects/{id}/specifications
PUT /api/v1/objects/{id}/specifications
GET /api/v1/objects/{id}/history
```

## 5. 接口约束

- 使用统一响应和错误结构。
- 对象、关系和规格接口必须执行权限校验。
- 更新操作不得静默丢失历史。
- API 版本使用 `/api/v1` 前缀。
- 文档通过 OpenAPI/Swagger 自动生成并保持同步。
