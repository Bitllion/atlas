<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { objectApi } from '../api/objects'
import { operationsApi } from '../api/operations'
import { loadUsers, useCatalog } from '../stores/catalog'
import type { InfrastructureObject, WorkOrder } from '../types'
const router = useRouter(); const items = ref<WorkOrder[]>([]); const objects = ref<InfrastructureObject[]>([]); const loading = ref(false); const total = ref(0); const page = ref(1); const status = ref(''); const type = ref(''); const pageSize = 20
const { userMap } = useCatalog()
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize))); const objectMap = computed(() => Object.fromEntries(objects.value.map(item => [item.id, item.name])))
const statusName: Record<string,string> = { CREATED:'已创建',ASSIGNED:'已分配',PROCESSING:'处理中',WAITING:'等待中',SUSPENDED:'已暂停',RESOLVED:'已解决',CLOSED:'已关闭',CANCELLED:'已取消',REOPENED:'已重开' }
const typeName: Record<string,string> = { FAULT:'故障',REPAIR:'维修',INSPECTION:'巡检',CHANGE:'变更' }; const priorityName: Record<string,string> = { CRITICAL:'紧急',HIGH:'高',MEDIUM:'中',LOW:'低' }
function format(value: string) { return new Date(value).toLocaleString('zh-CN') }
async function load() { loading.value=true; try { const {data}=await operationsApi.list({status:status.value||undefined,type:type.value||undefined,page:page.value,page_size:pageSize}); items.value=data.items; total.value=data.total } finally { loading.value=false } }
function filter(){ page.value=1; void load() }
onMounted(async()=>{ const [objectResult]=await Promise.all([objectApi.list({page:1,page_size:100}),load(),loadUsers()]); objects.value=objectResult.data.items })
</script>
<template><section class="page"><header class="page-header"><div><p class="eyebrow">OPERATIONS</p><h1>运维工单</h1><p class="muted">跟踪基础设施故障、维修与巡检处理过程</p></div><RouterLink class="button primary" to="/work-orders/new">新建工单</RouterLink></header>
<form class="filter-bar card" @submit.prevent="filter"><label><span>工单状态</span><select v-model="status"><option value="">全部状态</option><option v-for="(name,value) in statusName" :key="value" :value="value">{{name}}</option></select></label><label><span>工单类型</span><select v-model="type"><option value="">全部类型</option><option v-for="(name,value) in typeName" :key="value" :value="value">{{name}}</option></select></label><button class="button" type="submit">查询</button></form>
<div class="card table-card"><div v-if="loading" class="empty">正在加载…</div><div v-else-if="!items.length" class="empty">暂无工单</div><div v-else class="table-scroll"><table><thead><tr><th>工单号</th><th>标题</th><th>类型</th><th>状态</th><th>优先级</th><th>关联设备</th><th>创建时间</th><th>处理人</th></tr></thead><tbody><tr v-for="item in items" :key="item.id" class="clickable" @click="router.push(`/work-orders/${item.id}`)"><td class="name-cell">{{item.work_order_number}}</td><td>{{item.title}}</td><td>{{typeName[item.type]}}</td><td><span class="status" :class="item.status.toLowerCase()">{{statusName[item.status]}}</span></td><td><span class="priority" :class="item.priority.toLowerCase()">{{priorityName[item.priority]}}</span></td><td>{{objectMap[item.related_object_id]||item.related_object_id}}</td><td>{{format(item.created_at)}}</td><td>{{userMap[item.assigned_to||'']||'未分配'}}</td></tr></tbody></table></div><footer class="pagination"><span>共 {{total}} 条</span><div><button :disabled="page<=1" @click="page--;load()">上一页</button><span>第 {{page}} / {{totalPages}} 页</span><button :disabled="page>=totalPages" @click="page++;load()">下一页</button></div></footer></div>
</section></template>
