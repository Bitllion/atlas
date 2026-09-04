<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { assetApi } from '../api/assets'
import AssetActionModal from '../components/AssetActionModal.vue'
import { loadCatalogs, useCatalog } from '../stores/catalog'
import type { Asset } from '../types'

const router = useRouter()
const assets = ref<Asset[]>([]); const loading = ref(false); const total = ref(0); const page = ref(1); const status = ref(''); const action = ref<'stock' | 'deploy' | null>(null); const selected = ref<Asset | null>(null)
const { organizationMap, locationMap, objectTypeMap } = useCatalog()
const pageSize = 20
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const statusName: Record<string, string> = { REQUESTED: '已申请', APPROVED: '已批准', ORDERED: '已下单', PURCHASED: '已采购', RECEIVED: '已到货', STOCK: '库存中', IN_TRANSIT: '运输中', DEPLOYING: '部署中', DEPLOYED: '已部署', ACTIVE: '使用中', MAINTENANCE: '维护中', TRANSFERRED: '已调拨', RETIRED: '已退役', RECOVERED: '已回收' }
async function load() { loading.value = true; try { const { data } = await assetApi.list({ status: status.value || undefined, page: page.value, page_size: pageSize }); assets.value = data.items; total.value = data.total } finally { loading.value = false } }
function filter() { page.value = 1; void load() }
function open(item: Asset, kind: 'stock' | 'deploy') { selected.value = item; action.value = kind }
async function completed() { action.value = null; selected.value = null; await load() }
onMounted(async () => { await Promise.all([loadCatalogs(), load()]) })
</script>

<template><section class="page">
  <header class="page-header"><div><p class="eyebrow">ASSET LIFECYCLE</p><h1>资产管理</h1><p class="muted">管理资产从到货、入库到部署使用的完整生命周期</p></div><RouterLink class="button" to="/inventory">库存位置</RouterLink></header>
  <form class="filter-bar card compact-filter" @submit.prevent="filter"><label><span>生命周期状态</span><select v-model="status"><option value="">全部状态</option><option v-for="(name, value) in statusName" :key="value" :value="value">{{ name }}</option></select></label><button class="button" type="submit">查询</button></form>
  <div class="card table-card"><div v-if="loading" class="empty">正在加载…</div><div v-else-if="!assets.length" class="empty">暂无资产记录</div><div v-else class="table-scroll"><table><thead><tr><th>资产编号</th><th>关联设备名</th><th>类型</th><th>状态</th><th>所有者</th><th>位置</th><th>操作</th></tr></thead><tbody>
    <tr v-for="item in assets" :key="item.id" class="clickable" @click="router.push(`/assets/${item.id}`)"><td class="name-cell">{{ item.asset_number }}</td><td>{{ item.object.name }}</td><td>{{ objectTypeMap[item.object.object_type_id] || '—' }}</td><td><span class="status" :class="item.lifecycle_status.toLowerCase()">{{ statusName[item.lifecycle_status] || item.lifecycle_status }}</span></td><td>{{ organizationMap[item.owner_org_id || ''] || '—' }}</td><td>{{ locationMap[item.inventory_location_id || item.object.deployed_location_id || ''] || '—' }}</td><td class="actions" @click.stop><button v-if="item.lifecycle_status === 'RECEIVED'" class="link" @click="open(item, 'stock')">入库</button><button v-if="item.lifecycle_status === 'STOCK'" class="link" @click="open(item, 'deploy')">部署</button><RouterLink :to="`/assets/${item.id}`">详情</RouterLink></td></tr>
  </tbody></table></div><footer class="pagination"><span>共 {{ total }} 条</span><div><button :disabled="page <= 1" @click="page--; load()">上一页</button><span>第 {{ page }} / {{ totalPages }} 页</span><button :disabled="page >= totalPages" @click="page++; load()">下一页</button></div></footer></div>
  <AssetActionModal v-if="selected && action" :asset="selected" :action="action" @close="action = null; selected = null" @completed="completed" />
</section></template>
