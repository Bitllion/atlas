<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { loadCatalogs } from './stores/catalog'
const router = useRouter()
const globalQuery = ref('')
const toast = ref('')
let timer: number | undefined
function showError(event: Event) {
  toast.value = (event as CustomEvent<string>).detail
  window.clearTimeout(timer)
  timer = window.setTimeout(() => { toast.value = '' }, 4500)
}
function globalSearch() {
  const query = globalQuery.value.trim()
  if (query) void router.push({ path: '/search', query: { q: query } })
}
onMounted(() => { window.addEventListener('atlas-api-error', showError); void loadCatalogs() })
onBeforeUnmount(() => window.removeEventListener('atlas-api-error', showError))
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/dashboard"><span class="brand-mark">A</span><span>Atlas</span></RouterLink>
      <form class="global-search" role="search" @submit.prevent="globalSearch"><input v-model="globalQuery" aria-label="全局搜索" placeholder="搜索资源…" /><button aria-label="搜索" type="submit">⌕</button></form>
      <nav><RouterLink class="nav-item" to="/dashboard">Dashboard</RouterLink><p class="nav-label">基础设施</p><RouterLink class="nav-item" to="/objects">对象浏览器</RouterLink><RouterLink class="nav-item" to="/import">数据导入</RouterLink><p class="nav-label">资产运营</p><RouterLink class="nav-item" to="/assets">资产管理</RouterLink><RouterLink class="nav-item" to="/purchase-requests">采购申请</RouterLink><RouterLink class="nav-item" to="/inventory">库存管理</RouterLink><p class="nav-label">运维管理</p><RouterLink class="nav-item" to="/work-orders">运维工单</RouterLink><p class="nav-label">知识中心</p><RouterLink class="nav-item" to="/knowledge">知识库</RouterLink><p class="nav-label">系统管理</p><RouterLink class="nav-item" to="/admin/users">用户管理</RouterLink><RouterLink class="nav-item" to="/admin/organizations">组织管理</RouterLink></nav>
      <p class="sidebar-note">AI 基础设施智能运营管理平台</p>
    </aside>
    <main class="main-content"><RouterView /></main>
    <div v-if="toast" class="toast" role="alert">{{ toast }}</div>
  </div>
</template>
