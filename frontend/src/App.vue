<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
const toast = ref('')
let timer: number | undefined
function showError(event: Event) {
  toast.value = (event as CustomEvent<string>).detail
  window.clearTimeout(timer)
  timer = window.setTimeout(() => { toast.value = '' }, 4500)
}
onMounted(() => window.addEventListener('atlas-api-error', showError))
onBeforeUnmount(() => window.removeEventListener('atlas-api-error', showError))
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/objects"><span class="brand-mark">A</span><span>Atlas</span></RouterLink>
      <nav><p class="nav-label">基础设施</p><RouterLink class="nav-item" to="/objects">对象浏览器</RouterLink><RouterLink class="nav-item" to="/import">数据导入</RouterLink></nav>
      <p class="sidebar-note">AI 基础设施智能运营管理平台</p>
    </aside>
    <main class="main-content"><RouterView /></main>
    <div v-if="toast" class="toast" role="alert">{{ toast }}</div>
  </div>
</template>
