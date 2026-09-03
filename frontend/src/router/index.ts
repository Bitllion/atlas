import { createRouter, createWebHistory } from 'vue-router'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/objects' },
    { path: '/objects', name: 'objects', component: () => import('../views/ObjectListView.vue') },
    { path: '/objects/new', name: 'object-create', component: () => import('../views/ObjectFormView.vue') },
    { path: '/objects/:id', name: 'object-detail', component: () => import('../views/ObjectDetailView.vue') },
    { path: '/objects/:id/edit', name: 'object-edit', component: () => import('../views/ObjectFormView.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/objects' },
  ],
})
