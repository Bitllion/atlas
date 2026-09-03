<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { objectApi } from '../api/objects'
import type { InfrastructureObject, ObjectType } from '../types'

const router = useRouter()
const objects = ref<InfrastructureObject[]>([])
const types = ref<ObjectType[]>([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const name = ref('')
const objectTypeId = ref('')
const status = ref('')
const typeMap = computed(() => Object.fromEntries(types.value.map((item) => [item.id, item.display_name || item.name])))
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

async function load() {
  loading.value = true
  try {
    const { data } = await objectApi.list({ page: page.value, page_size: pageSize, name: name.value || undefined, object_type_id: objectTypeId.value || undefined, status: status.value || undefined })
    objects.value = data.items; total.value = data.total
  } finally { loading.value = false }
}
function search() { page.value = 1; void load() }
function changePage(value: number) { page.value = value; void load() }
async function remove(item: InfrastructureObject) {
  if (!window.confirm(`确认删除对象“${item.name}”吗？该操作为软删除。`)) return
  await objectApi.remove(item.id)
  if (objects.value.length === 1 && page.value > 1) page.value--
  await load()
}
onMounted(async () => { const response = await objectApi.types(); types.value = response.data.items; await load() })
</script>

<template>
  <section class="page">
    <header class="page-header"><div><p class="eyebrow">INFRASTRUCTURE CORE</p><h1>对象浏览器</h1><p class="muted">统一查看和管理基础设施对象</p></div><RouterLink class="button primary" to="/objects/new">+ 新建对象</RouterLink></header>
    <form class="filter-bar card" @submit.prevent="search">
      <label><span>名称</span><input v-model.trim="name" placeholder="搜索对象名称" /></label>
      <label><span>对象类型</span><select v-model="objectTypeId"><option value="">全部类型</option><option v-for="item in types" :key="item.id" :value="item.id">{{ item.display_name || item.name }}</option></select></label>
      <label><span>状态</span><select v-model="status"><option value="">全部状态</option><option value="PLANNED">计划中</option><option value="ACTIVE">运行中</option><option value="INACTIVE">未启用</option><option value="MAINTENANCE">维护中</option><option value="RETIRED">已退役</option></select></label>
      <button class="button" type="submit">查询</button>
    </form>
    <div class="card table-card">
      <div v-if="loading" class="empty">正在加载…</div>
      <div v-else-if="!objects.length" class="empty">没有符合条件的对象</div>
      <div v-else class="table-scroll"><table><thead><tr><th>名称</th><th>类型</th><th>状态</th><th>制造商</th><th>型号</th><th>序列号</th><th>创建时间</th><th>操作</th></tr></thead><tbody>
        <tr v-for="item in objects" :key="item.id" class="clickable" @click="router.push(`/objects/${item.id}`)">
          <td class="name-cell">{{ item.name }}</td><td>{{ typeMap[item.object_type_id] || '—' }}</td><td><span class="status" :class="item.status.toLowerCase()">{{ item.status }}</span></td><td>{{ item.manufacturer || '—' }}</td><td>{{ item.model || '—' }}</td><td>{{ item.serial_number || '—' }}</td><td>{{ new Date(item.created_at).toLocaleString('zh-CN') }}</td>
          <td class="actions" @click.stop><RouterLink :to="`/objects/${item.id}/edit`">编辑</RouterLink><button class="link danger" @click="remove(item)">删除</button></td>
        </tr></tbody></table></div>
      <footer class="pagination"><span>共 {{ total }} 条</span><div><button :disabled="page <= 1" @click="changePage(page - 1)">上一页</button><span>第 {{ page }} / {{ totalPages }} 页</span><button :disabled="page >= totalPages" @click="changePage(page + 1)">下一页</button></div></footer>
    </div>
  </section>
</template>
