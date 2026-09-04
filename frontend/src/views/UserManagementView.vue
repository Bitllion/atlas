<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { adminApi } from '../api/admin'
import { loadCatalogs, loadUsers, useCatalog } from '../stores/catalog'
import type { User } from '../types'

const { state } = useCatalog()
const items = ref<User[]>([]), total = ref(0), page = ref(1), search = ref(''), loading = ref(false), saving = ref(false), modal = ref(false)
const pageSize = 20
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const form = reactive({ username: '', full_name: '', email: '', organization_id: '' })
async function load() { loading.value = true; try { const { data } = await adminApi.users({ search: search.value || undefined, page: page.value, page_size: pageSize }); items.value = data.items; total.value = data.total } finally { loading.value = false } }
function query() { page.value = 1; void load() }
function openCreate() { Object.assign(form, { username: '', full_name: '', email: '', organization_id: state.organizations.find(item => item.is_active)?.id || '' }); modal.value = true }
async function create() { saving.value = true; try { await adminApi.createUser({ ...form, full_name: form.full_name || null }); modal.value = false; await Promise.all([load(), loadUsers(true)]) } finally { saving.value = false } }
async function toggle(item: User) { if (!window.confirm(`确认${item.is_active ? '停用' : '启用'}用户“${item.username}”吗？`)) return; await adminApi.updateUser(item.id, { is_active: !item.is_active }); await Promise.all([load(), loadUsers(true)]) }
onMounted(async () => { await loadCatalogs(); await load() })
</script>
<template><section class="page"><header class="page-header"><div><p class="eyebrow">SYSTEM MANAGEMENT</p><h1>用户管理</h1><p class="muted">维护平台用户、所属组织与启用状态</p></div><button class="button primary" @click="openCreate">+ 新建用户</button></header>
<form class="filter-bar card compact-filter" @submit.prevent="query"><label><span>用户名或姓名</span><input v-model.trim="search" placeholder="输入关键字" /></label><button class="button">查询</button></form>
<div class="card table-card"><div v-if="loading" class="empty">正在加载…</div><div v-else-if="!items.length" class="empty">暂无用户</div><div v-else class="table-scroll"><table><thead><tr><th>用户名</th><th>姓名</th><th>邮箱</th><th>所属组织</th><th>状态</th><th>操作</th></tr></thead><tbody><tr v-for="item in items" :key="item.id"><td class="name-cell">{{item.username}}</td><td>{{item.full_name||'—'}}</td><td>{{item.email}}</td><td>{{item.organization_name||'—'}}</td><td><span class="status" :class="item.is_active?'active':'inactive'">{{item.is_active?'已启用':'已停用'}}</span></td><td><button class="link" :class="{danger:item.is_active}" @click="toggle(item)">{{item.is_active?'停用':'启用'}}</button></td></tr></tbody></table></div><footer class="pagination"><span>共 {{total}} 条</span><div><button :disabled="page<=1" @click="page--;load()">上一页</button><span>第 {{page}} / {{totalPages}} 页</span><button :disabled="page>=totalPages" @click="page++;load()">下一页</button></div></footer></div>
<div v-if="modal" class="modal-mask" @click.self="modal=false"><form class="modal card" @submit.prevent="create"><header><div><p class="eyebrow">CREATE USER</p><h2>新建用户</h2></div><button class="modal-close" type="button" @click="modal=false">×</button></header><div class="form-grid"><label><span>用户名 *</span><input v-model.trim="form.username" required maxlength="100" /></label><label><span>姓名</span><input v-model.trim="form.full_name" maxlength="255" /></label><label><span>邮箱 *</span><input v-model.trim="form.email" required type="email" maxlength="255" /></label><label><span>所属组织 *</span><select v-model="form.organization_id" required><option value="" disabled>请选择组织</option><option v-for="org in state.organizations.filter(item=>item.is_active)" :key="org.id" :value="org.id">{{org.name}}</option></select></label></div><footer><button class="button" type="button" @click="modal=false">取消</button><button class="button primary" :disabled="saving">{{saving?'创建中…':'创建用户'}}</button></footer></form></div>
</section></template>
