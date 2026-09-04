import type { RouteLocationNormalizedLoaded } from 'vue-router'

export interface BreadcrumbItem { label: string; path?: string }

const routeNavigation: Record<string, { title: string; breadcrumbs: BreadcrumbItem[] }> = {
  login: { title: '登录', breadcrumbs: [] },
  dashboard: { title: '工作台', breadcrumbs: [{ label: '工作台' }] },
  search: { title: '搜索结果', breadcrumbs: [{ label: '工作台', path: '/dashboard' }, { label: '搜索结果' }] },
  objects: { title: '对象管理', breadcrumbs: [{ label: '对象管理' }, { label: '对象' }] },
  'object-create': { title: '新建对象', breadcrumbs: [{ label: '对象管理' }, { label: '对象', path: '/objects' }, { label: '新建对象' }] },
  'object-detail': { title: '对象详情', breadcrumbs: [{ label: '对象管理' }, { label: '对象', path: '/objects' }, { label: '对象详情' }] },
  'object-edit': { title: '编辑对象', breadcrumbs: [{ label: '对象管理' }, { label: '对象', path: '/objects' }, { label: '编辑对象' }] },
  import: { title: '数据导入', breadcrumbs: [{ label: '对象管理' }, { label: '数据导入' }] },
  'import-history': { title: '导入历史', breadcrumbs: [{ label: '对象管理' }, { label: '导入历史' }] },
  assets: { title: '资产管理', breadcrumbs: [{ label: '资产管理' }, { label: '资产台账' }] },
  'asset-detail': { title: '资产详情', breadcrumbs: [{ label: '资产管理' }, { label: '资产台账', path: '/assets' }, { label: '资产详情' }] },
  'purchase-requests': { title: '采购申请', breadcrumbs: [{ label: '资产管理' }, { label: '采购申请' }] },
  inventory: { title: '库存管理', breadcrumbs: [{ label: '资产管理' }, { label: '库存管理' }] },
  'work-orders': { title: '运维工单', breadcrumbs: [{ label: '运维管理' }, { label: '运维工单' }] },
  'work-order-create': { title: '新建工单', breadcrumbs: [{ label: '运维管理' }, { label: '运维工单', path: '/work-orders' }, { label: '新建工单' }] },
  'work-order-detail': { title: '工单详情', breadcrumbs: [{ label: '运维管理' }, { label: '运维工单', path: '/work-orders' }, { label: '工单详情' }] },
  approvals: { title: '我的审批', breadcrumbs: [{ label: '运维管理' }, { label: '我的审批' }] },
  knowledge: { title: '知识库', breadcrumbs: [{ label: '知识中心' }, { label: '知识库' }] },
  'knowledge-create': { title: '新建文章', breadcrumbs: [{ label: '知识中心' }, { label: '知识库', path: '/knowledge' }, { label: '新建文章' }] },
  'knowledge-detail': { title: '文章详情', breadcrumbs: [{ label: '知识中心' }, { label: '知识库', path: '/knowledge' }, { label: '文章详情' }] },
  quality: { title: '数据质量', breadcrumbs: [{ label: '数据治理' }, { label: '数据质量' }] },
  'admin-users': { title: '用户管理', breadcrumbs: [{ label: '系统管理' }, { label: '用户管理' }] },
  'admin-organizations': { title: '组织管理', breadcrumbs: [{ label: '系统管理' }, { label: '组织管理' }] },
}

export function navigationFor(route: RouteLocationNormalizedLoaded) {
  return routeNavigation[String(route.name)] || { title: 'Atlas', breadcrumbs: [] }
}
