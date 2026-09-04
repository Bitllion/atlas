import { createRouter, createWebHistory } from 'vue-router'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue') },
    { path: '/search', name: 'search', component: () => import('../views/SearchView.vue') },
    { path: '/knowledge', name: 'knowledge', component: () => import('../views/KnowledgeListView.vue') },
    { path: '/knowledge/new', name: 'knowledge-create', component: () => import('../views/KnowledgeCreateView.vue') },
    { path: '/knowledge/:id', name: 'knowledge-detail', component: () => import('../views/KnowledgeDetailView.vue') },
    { path: '/objects', name: 'objects', component: () => import('../views/ObjectListView.vue') },
    { path: '/objects/new', name: 'object-create', component: () => import('../views/ObjectFormView.vue') },
    { path: '/objects/:id', name: 'object-detail', component: () => import('../views/ObjectDetailView.vue') },
    { path: '/objects/:id/edit', name: 'object-edit', component: () => import('../views/ObjectFormView.vue') },
    { path: '/import', name: 'import', component: () => import('../views/ImportView.vue') },
    { path: '/imports', name: 'import-history', component: () => import('../views/ImportHistoryView.vue') },
    { path: '/import/history', redirect: '/imports' },
    { path: '/assets', name: 'assets', component: () => import('../views/AssetListView.vue') },
    { path: '/assets/:id', name: 'asset-detail', component: () => import('../views/AssetDetailView.vue') },
    { path: '/purchase-requests', name: 'purchase-requests', component: () => import('../views/PurchaseRequestsView.vue') },
    { path: '/inventory', name: 'inventory', component: () => import('../views/InventoryView.vue') },
    { path: '/work-orders', name: 'work-orders', component: () => import('../views/WorkOrderListView.vue') },
    { path: '/work-orders/new', name: 'work-order-create', component: () => import('../views/WorkOrderCreateView.vue') },
    { path: '/work-orders/:id', name: 'work-order-detail', component: () => import('../views/WorkOrderDetailView.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/objects' },
  ],
})
