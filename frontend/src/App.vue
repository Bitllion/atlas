<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { loadCatalogs } from './stores/catalog'
import { currentUser, logout } from './stores/auth'
import { notificationsApi } from './api/notifications'
import type { Notification } from './types'

const router = useRouter()
const route = useRoute()
const isLoginPage = computed(() => route.path === '/login')
const globalQuery = ref('')
const toast = ref('')
const unreadCount = ref(0)
const notifications = ref<Notification[]>([])
const showNotifications = ref(false)
const hasRoles = computed(() => currentUser.value?.roles && currentUser.value.roles.length > 0)

let timer: number | undefined
let pollTimer: number | undefined

function showError(event: Event) {
  toast.value = (event as CustomEvent<string>).detail
  window.clearTimeout(timer)
  timer = window.setTimeout(() => { toast.value = '' }, 4500)
}

function globalSearch() {
  const query = globalQuery.value.trim()
  if (query) void router.push({ path: '/search', query: { q: query } })
}

function signOut() {
  logout()
  void router.replace('/login')
}

async function loadUnreadCount() {
  if (!localStorage.getItem('atlas_token')) return
  try {
    const { data } = await notificationsApi.unreadCount()
    unreadCount.value = data.count
  } catch {
    // 静默失败
  }
}

async function loadNotifications() {
  try {
    const { data } = await notificationsApi.my(1, 10)
    notifications.value = data.items
  } catch {
    // 静默失败
  }
}

async function toggleNotifications() {
  showNotifications.value = !showNotifications.value
  if (showNotifications.value) await loadNotifications()
}

async function handleNotificationClick(notification: Notification) {
  if (!notification.is_read) {
    await notificationsApi.markRead(notification.id)
    await loadUnreadCount()
  }
  showNotifications.value = false

  // 根据实体类型跳转
  if (notification.entity_type === 'WORK_ORDER' && notification.entity_id) {
    void router.push(`/work-orders/${notification.entity_id}`)
  } else if (notification.entity_type === 'PURCHASE_REQUEST' && notification.entity_id) {
    void router.push('/purchase-requests')
  }
}

async function markAllAsRead() {
  await notificationsApi.markAllRead()
  await loadUnreadCount()
  await loadNotifications()
}

function startPolling() {
  void loadUnreadCount()
  pollTimer = window.setInterval(() => { void loadUnreadCount() }, 30000) // 30秒轮询
}

function stopPolling() {
  if (pollTimer) window.clearInterval(pollTimer)
}

onMounted(() => {
  window.addEventListener('atlas-api-error', showError)
  if (localStorage.getItem('atlas_token')) {
    void loadCatalogs()
    startPolling()
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('atlas-api-error', showError)
  stopPolling()
})
</script>

<template>
  <RouterView v-if="isLoginPage" />
  <div v-else class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/dashboard"><span class="brand-mark">A</span><span>Atlas</span></RouterLink>
      <div class="sidebar-user">
        <div>
          <span>当前用户</span>
          <strong>{{ currentUser?.username || '已登录用户' }}</strong>
        </div>
        <div class="user-actions">
          <button type="button" class="notification-bell" @click="toggleNotifications">
            🔔
            <span v-if="unreadCount > 0" class="badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
          </button>
          <button type="button" @click="signOut">退出登录</button>
        </div>
      </div>
      <div v-if="showNotifications" class="notifications-dropdown">
        <div class="notifications-header">
          <strong>通知</strong>
          <button v-if="notifications.length > 0" class="link" @click="markAllAsRead">全部已读</button>
        </div>
        <div v-if="notifications.length === 0" class="empty-notifications">暂无通知</div>
        <div v-else class="notifications-list">
          <div
            v-for="notification in notifications"
            :key="notification.id"
            class="notification-item"
            :class="{ unread: !notification.is_read }"
            @click="handleNotificationClick(notification)"
          >
            <div class="notification-type">{{ notification.type === 'WORKFLOW_TASK' ? '📋' : '📢' }}</div>
            <div class="notification-content">
              <div class="notification-title">{{ notification.title }}</div>
              <div class="notification-time">{{ new Date(notification.created_at).toLocaleString('zh-CN') }}</div>
            </div>
          </div>
        </div>
      </div>
      <form class="global-search" role="search" @submit.prevent="globalSearch">
        <input v-model="globalQuery" aria-label="全局搜索" placeholder="搜索资源…" />
        <button aria-label="搜索" type="submit">⌕</button>
      </form>
      <nav>
        <RouterLink class="nav-item" to="/dashboard">Dashboard</RouterLink>
        <p class="nav-label">基础设施</p>
        <RouterLink class="nav-item" to="/objects">对象浏览器</RouterLink>
        <RouterLink class="nav-item" to="/import">数据导入</RouterLink>
        <p class="nav-label">资产运营</p>
        <RouterLink class="nav-item" to="/assets">资产管理</RouterLink>
        <RouterLink class="nav-item" to="/purchase-requests">采购申请</RouterLink>
        <RouterLink class="nav-item" to="/inventory">库存管理</RouterLink>
        <p class="nav-label">运维管理</p>
        <RouterLink class="nav-item" to="/work-orders">运维工单</RouterLink>
        <RouterLink v-if="hasRoles" class="nav-item" to="/approvals">我的审批</RouterLink>
        <p class="nav-label">数据质量</p>
        <RouterLink class="nav-item" to="/quality">数据质量</RouterLink>
        <p class="nav-label">知识中心</p>
        <RouterLink class="nav-item" to="/knowledge">知识库</RouterLink>
        <p class="nav-label">系统管理</p>
        <RouterLink class="nav-item" to="/admin/users">用户管理</RouterLink>
        <RouterLink class="nav-item" to="/admin/organizations">组织管理</RouterLink>
      </nav>
      <p class="sidebar-note">AI 基础设施智能运营管理平台</p>
    </aside>
    <main class="main-content"><RouterView /></main>
    <div v-if="toast" class="toast" role="alert">{{ toast }}</div>
  </div>
</template>
