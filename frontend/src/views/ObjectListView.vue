<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { IconDelete, IconEdit, IconPlus, IconSearch } from '@arco-design/web-vue/es/icon'
import { objectApi } from '../api/objects'
import type { InfrastructureObject, ObjectType, ObjectStatus } from '../types'

const router = useRouter()
const objects = ref<InfrastructureObject[]>([]), types = ref<ObjectType[]>([])
const loading = ref(false), deleting = ref(false), deleteVisible = ref(false)
const pendingDelete = ref<InfrastructureObject | null>(null)
const total = ref(0), page = ref(1), pageSize = 20
const name = ref(''), objectTypeId = ref(''), status = ref('')
const typeMap = computed(() => Object.fromEntries(types.value.map((item) => [item.id, item.display_name || item.name])))
const statusOptions = [{ value: 'PLANNED', label: '计划中' }, { value: 'ACTIVE', label: '运行中' }, { value: 'INACTIVE', label: '未启用' }, { value: 'MAINTENANCE', label: '维护中' }, { value: 'RETIRED', label: '已退役' }]
const statusLabel = (value: ObjectStatus) => statusOptions.find((item) => item.value === value)?.label || value
const statusColor = (value: ObjectStatus) => ({ PLANNED: 'blue', ACTIVE: 'green', INACTIVE: 'gray', MAINTENANCE: 'orange', RETIRED: 'red' }[value] || 'gray')

async function load() { loading.value = true; try { const { data } = await objectApi.list({ page: page.value, page_size: pageSize, name: name.value || undefined, object_type_id: objectTypeId.value || undefined, status: status.value || undefined }); objects.value = data.items; total.value = data.total } finally { loading.value = false } }
function search() { page.value = 1; void load() }
function reset() { name.value = ''; objectTypeId.value = ''; status.value = ''; search() }
function changePage(value: number) { page.value = value; void load() }
function openObject(item: unknown) { void router.push(`/objects/${(item as InfrastructureObject).id}`) }
function askRemove(item: InfrastructureObject) { pendingDelete.value = item; deleteVisible.value = true }
async function confirmRemove() { if (!pendingDelete.value) return; deleting.value = true; try { await objectApi.remove(pendingDelete.value.id); deleteVisible.value = false; if (objects.value.length === 1 && page.value > 1) page.value--; await load(); Message.success('对象删除成功') } finally { deleting.value = false } }
onMounted(async () => { types.value = (await objectApi.types()).data.items; await load() })
</script>

<template>
  <section class="page arco-page">
    <header class="page-header"><div><p class="eyebrow">基础设施对象</p><h1>对象浏览器</h1><p class="muted">统一查看和管理基础设施对象</p></div><a-button type="primary" @click="router.push('/objects/new')"><template #icon><IconPlus /></template>新建对象</a-button></header>
    <a-card class="arco-filter-card" :bordered="false">
      <a-form :model="{}" layout="inline" @submit.prevent="search">
        <a-form-item label="名称"><a-input v-model="name" placeholder="搜索对象名称" allow-clear /></a-form-item>
        <a-form-item label="对象类型"><a-select v-model="objectTypeId" placeholder="全部类型" allow-clear><a-option value="">全部类型</a-option><a-option v-for="item in types" :key="item.id" :value="item.id">{{ item.display_name || item.name }}</a-option></a-select></a-form-item>
        <a-form-item label="状态"><a-select v-model="status" placeholder="全部状态" allow-clear><a-option value="">全部状态</a-option><a-option v-for="item in statusOptions" :key="item.value" :value="item.value">{{ item.label }}</a-option></a-select></a-form-item>
        <a-form-item><a-space><a-button type="primary" html-type="submit"><template #icon><IconSearch /></template>查询</a-button><a-button @click="reset">重置</a-button></a-space></a-form-item>
      </a-form>
    </a-card>
    <a-card class="arco-table-card" :bordered="false">
      <a-table :data="objects" :loading="loading" :pagination="false" row-key="id" :scroll="{ x: 1100 }" @row-click="openObject">
        <template #columns>
          <a-table-column title="名称" data-index="name" :width="180"><template #cell="{ record }"><a-link class="object-name">{{ record.name }}</a-link></template></a-table-column>
          <a-table-column title="类型" :width="130"><template #cell="{ record }">{{ typeMap[record.object_type_id] || '—' }}</template></a-table-column>
          <a-table-column title="状态" :width="100"><template #cell="{ record }"><a-tag :color="statusColor(record.status)" bordered>{{ statusLabel(record.status) }}</a-tag></template></a-table-column>
          <a-table-column title="制造商" data-index="manufacturer" :width="130"><template #cell="{ record }">{{ record.manufacturer || '—' }}</template></a-table-column>
          <a-table-column title="型号" data-index="model" :width="130"><template #cell="{ record }">{{ record.model || '—' }}</template></a-table-column>
          <a-table-column title="序列号" data-index="serial_number" :width="160"><template #cell="{ record }">{{ record.serial_number || '—' }}</template></a-table-column>
          <a-table-column title="创建时间" :width="180"><template #cell="{ record }">{{ new Date(record.created_at).toLocaleString('zh-CN') }}</template></a-table-column>
          <a-table-column title="操作" fixed="right" :width="190"><template #cell="{ record }"><div class="table-actions" @click.stop><a-button type="text" size="small" @click="router.push(`/objects/${record.id}`)">详情</a-button><a-button type="text" size="small" @click="router.push(`/objects/${record.id}/edit`)"><template #icon><IconEdit /></template>编辑</a-button><a-button type="text" status="danger" size="small" @click="askRemove(record)"><template #icon><IconDelete /></template>删除</a-button></div></template></a-table-column>
        </template>
        <template #empty><a-empty class="atlas-empty-guide" description="暂无对象，可新建或批量导入"><a-space><a-button type="primary" @click="router.push('/objects/new')">新建对象</a-button><a-button @click="router.push('/import')">导入对象</a-button></a-space></a-empty></template>
      </a-table>
      <div class="arco-pagination"><span>共 {{ total }} 条</span><a-pagination :current="page" :page-size="pageSize" :total="total" :show-total="false" @change="changePage" /></div>
    </a-card>
    <a-modal v-model:visible="deleteVisible" title="删除对象" :ok-loading="deleting" ok-text="确认删除" cancel-text="取消" simple @ok="confirmRemove"><p>确认删除对象“{{ pendingDelete?.name }}”吗？该操作为软删除。</p></a-modal>
  </section>
</template>
