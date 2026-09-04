<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import { IconApps, IconArchive, IconBook, IconCheckCircle, IconDashboard, IconDown, IconFile, IconHistory, IconImport, IconMenuFold, IconMenuUnfold, IconMindMapping, IconNotification, IconPoweroff, IconSearch, IconStorage, IconTool, IconUser } from '@arco-design/web-vue/es/icon'
import { loadCatalogs } from './stores/catalog'
import { currentUser, logout } from './stores/auth'
import { notificationsApi } from './api/notifications'
import type { Notification } from './types'
import { navigationFor } from './navigation'

const router = useRouter(), route = useRoute()
const isLoginPage = computed(() => route.path === '/login')
const collapsed = ref(false), globalQuery = ref(''), toast = ref(''), unreadCount = ref(0)
const notifications = ref<Notification[]>([]), showNotifications = ref(false)
const hasRoles = computed(() => Boolean(currentUser.value?.roles?.length))
const isAdmin = computed(() => currentUser.value?.roles?.some((role) => role.toLowerCase() === 'admin'))
const displayName = computed(() => currentUser.value?.full_name || currentUser.value?.username || '已登录用户')
const roleName = computed(() => currentUser.value?.roles?.join('、') || '普通用户')
const breadcrumbs = computed(() => navigationFor(route).breadcrumbs)
const selectedKey = computed(() => {
  const path = route.path
  if (path.startsWith('/objects')) return '/objects'
  if (path === '/import') return '/import'
  if (path.startsWith('/imports') || path.startsWith('/import/history')) return '/imports'
  if (path.startsWith('/assets')) return '/assets'
  if (path.startsWith('/work-orders')) return '/work-orders'
  if (path.startsWith('/knowledge')) return '/knowledge'
  if (path.startsWith('/admin/users')) return '/admin/users'
  if (path.startsWith('/admin/organizations')) return '/admin/organizations'
  return path
})
let timer: number | undefined, pollTimer: number | undefined

function showError(event: Event) { toast.value = (event as CustomEvent<string>).detail; window.clearTimeout(timer); timer = window.setTimeout(() => { toast.value = '' }, 4500) }
function globalSearch() { const query = globalQuery.value.trim(); if (query) void router.push({ path: '/search', query: { q: query } }) }
function signOut() { logout(); void router.replace('/login') }
function navigate(key: string) { void router.push(key) }
async function loadUnreadCount() { if (!localStorage.getItem('atlas_token')) return; try { unreadCount.value = (await notificationsApi.unreadCount()).data.count } catch { /* 静默失败 */ } }
async function loadNotifications() { try { notifications.value = (await notificationsApi.my(1, 10)).data.items } catch { /* 静默失败 */ } }
async function openNotifications(visible: boolean) { showNotifications.value = visible; if (visible) await loadNotifications() }
async function handleNotificationClick(item: Notification) {
  if (!item.is_read) { await notificationsApi.markRead(item.id); await loadUnreadCount() }
  showNotifications.value = false
  if (item.entity_type === 'WORK_ORDER' && item.entity_id) void router.push(`/work-orders/${item.entity_id}`)
  else if (item.entity_type === 'PURCHASE_REQUEST' && item.entity_id) void router.push('/purchase-requests')
}
async function markAllAsRead() { await notificationsApi.markAllRead(); await Promise.all([loadUnreadCount(), loadNotifications()]) }
function startPolling() { void loadUnreadCount(); pollTimer = window.setInterval(() => { void loadUnreadCount() }, 30000) }
function stopPolling() { if (pollTimer) window.clearInterval(pollTimer) }
onMounted(() => { window.addEventListener('atlas-api-error', showError); if (localStorage.getItem('atlas_token')) { void loadCatalogs(); startPolling() } })
onBeforeUnmount(() => { window.removeEventListener('atlas-api-error', showError); stopPolling() })
</script>

<template>
  <RouterView v-if="isLoginPage" />
  <a-layout v-else class="atlas-layout">
    <a-layout-sider class="atlas-sider" :width="220" :collapsed-width="48" :collapsed="collapsed" collapsible breakpoint="lg" :hide-trigger="true" @collapse="collapsed = $event">
      <button class="atlas-brand" type="button" aria-label="返回工作台" @click="router.push('/dashboard')"><span class="atlas-brand-mark">A</span><span v-if="!collapsed" class="atlas-brand-name">Atlas</span></button>
      <a-menu class="atlas-menu" mode="vertical" :selected-keys="[selectedKey]" @menu-item-click="navigate">
        <a-menu-item key="/dashboard"><template #icon><a-tooltip content="工作台" position="right" :disabled="!collapsed"><IconDashboard /></a-tooltip></template>工作台</a-menu-item>
        <a-menu-item-group title="对象管理">
          <a-menu-item key="/objects"><template #icon><a-tooltip content="对象" position="right" :disabled="!collapsed"><IconApps /></a-tooltip></template>对象</a-menu-item>
          <a-menu-item key="/import"><template #icon><a-tooltip content="数据导入" position="right" :disabled="!collapsed"><IconImport /></a-tooltip></template>数据导入</a-menu-item>
          <a-menu-item key="/imports"><template #icon><a-tooltip content="导入历史" position="right" :disabled="!collapsed"><IconHistory /></a-tooltip></template>导入历史</a-menu-item>
        </a-menu-item-group>
        <a-menu-item-group title="资产管理">
          <a-menu-item key="/assets"><template #icon><a-tooltip content="资产台账" position="right" :disabled="!collapsed"><IconArchive /></a-tooltip></template>资产台账</a-menu-item>
          <a-menu-item key="/purchase-requests"><template #icon><a-tooltip content="采购申请" position="right" :disabled="!collapsed"><IconFile /></a-tooltip></template>采购申请</a-menu-item>
          <a-menu-item key="/inventory"><template #icon><a-tooltip content="库存管理" position="right" :disabled="!collapsed"><IconStorage /></a-tooltip></template>库存管理</a-menu-item>
        </a-menu-item-group>
        <a-menu-item-group title="运维管理">
          <a-menu-item key="/work-orders"><template #icon><a-tooltip content="运维工单" position="right" :disabled="!collapsed"><IconTool /></a-tooltip></template>运维工单</a-menu-item>
          <a-menu-item v-if="hasRoles" key="/approvals"><template #icon><a-tooltip content="我的审批" position="right" :disabled="!collapsed"><IconCheckCircle /></a-tooltip></template>我的审批</a-menu-item>
        </a-menu-item-group>
        <a-menu-item key="/knowledge"><template #icon><a-tooltip content="知识库" position="right" :disabled="!collapsed"><IconBook /></a-tooltip></template>知识库</a-menu-item>
        <a-menu-item key="/quality"><template #icon><a-tooltip content="数据质量" position="right" :disabled="!collapsed"><IconCheckCircle /></a-tooltip></template>数据质量</a-menu-item>
        <a-menu-item-group v-if="isAdmin" title="系统管理">
          <a-menu-item key="/admin/users"><template #icon><a-tooltip content="用户管理" position="right" :disabled="!collapsed"><IconUser /></a-tooltip></template>用户管理</a-menu-item>
          <a-menu-item key="/admin/organizations"><template #icon><a-tooltip content="组织管理" position="right" :disabled="!collapsed"><IconMindMapping /></a-tooltip></template>组织管理</a-menu-item>
        </a-menu-item-group>
      </a-menu>
      <div class="sider-collapse-area">
        <a-tooltip :content="collapsed ? '展开侧边栏' : '收起侧边栏'" position="right" :disabled="!collapsed">
          <a-button type="text" class="collapse-button" :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'" @click="collapsed = !collapsed"><IconMenuUnfold v-if="collapsed" /><IconMenuFold v-else /></a-button>
        </a-tooltip>
      </div>
    </a-layout-sider>
    <a-layout class="atlas-main-layout" :style="{ marginLeft: collapsed ? '48px' : '220px' }">
      <a-layout-header class="atlas-header">
        <div class="header-actions">
          <a-input-search v-model="globalQuery" class="header-search" placeholder="搜索资源" allow-clear @search="globalSearch" @press-enter="globalSearch"><template #prefix><IconSearch /></template></a-input-search>
          <a-popover trigger="click" position="br" :popup-visible="showNotifications" @popup-visible-change="openNotifications">
            <a-badge :count="unreadCount" :max-count="99"><a-button type="text" shape="circle" aria-label="通知"><IconNotification /></a-button></a-badge>
            <template #content><div class="notification-panel"><div class="notification-panel-header"><strong>通知</strong><a-link v-if="notifications.length" @click="markAllAsRead">全部已读</a-link></div><a-empty v-if="!notifications.length" description="暂无通知" /><div v-else class="notification-panel-list"><button v-for="item in notifications" :key="item.id" class="notification-row" :class="{ unread: !item.is_read }" @click="handleNotificationClick(item)"><span class="notification-dot" /><span><strong>{{ item.title }}</strong><small>{{ new Date(item.created_at).toLocaleString('zh-CN') }}</small></span></button></div></div></template>
          </a-popover>
          <a-dropdown trigger="click"><button class="user-entry" type="button"><a-avatar :size="32">{{ displayName.slice(0, 1).toUpperCase() }}</a-avatar><span class="user-meta"><strong>{{ displayName }}</strong><small>{{ roleName }}</small></span><IconDown /></button><template #content><a-doption @click="signOut"><template #icon><IconPoweroff /></template>退出登录</a-doption></template></a-dropdown>
        </div>
      </a-layout-header>
      <a-layout-content class="atlas-content">
        <a-breadcrumb v-if="breadcrumbs.length" class="atlas-breadcrumb">
          <a-breadcrumb-item v-for="item in breadcrumbs" :key="item.label"><a-link v-if="item.path" @click="router.push(item.path)">{{ item.label }}</a-link><span v-else>{{ item.label }}</span></a-breadcrumb-item>
        </a-breadcrumb>
        <RouterView />
      </a-layout-content>
    </a-layout>
    <div v-if="toast" class="toast" role="alert">{{ toast }}</div>
  </a-layout>
</template>
