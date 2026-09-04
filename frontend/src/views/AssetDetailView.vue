<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { assetApi } from '../api/assets'
import { objectApi } from '../api/objects'
import AssetActionModal from '../components/AssetActionModal.vue'
import { loadCatalogs, useCatalog } from '../stores/catalog'
import type { AssetDetail, LifecycleEvent, ObjectType } from '../types'

type AssetAction = 'stock' | 'deploy' | 'transfer' | 'complete-transfer' | 'retire' | 'recover'
const route = useRoute(); const asset = ref<AssetDetail | null>(null); const events = ref<LifecycleEvent[]>([]); const types = ref<ObjectType[]>([]); const action = ref<AssetAction | null>(null)
const { organizationMap, locationMap } = useCatalog()
const typeName = computed(() => types.value.find((item) => item.id === asset.value?.object.object_type_id)?.display_name || types.value.find((item) => item.id === asset.value?.object.object_type_id)?.name || '—')
const labels: Record<string, string> = { REQUESTED: '提交采购申请', APPROVED: '采购申请批准', RECEIVED: '到货验收', STOCK: '资产入库', DEPLOYED: '完成部署', ACTIVE: '投入使用', REJECTED: '申请驳回' }
const statusName: Record<string, string> = { RECEIVED: '已到货', STOCK: '库存中', ACTIVE: '使用中', DEPLOYED: '已部署', MAINTENANCE: '维护中', TRANSFERRED: '调拨中', RETIRED: '已退役', RECOVERED: '已撤销' }
function date(value: string | null | undefined) { return value ? new Date(value).toLocaleString('zh-CN') : '—' }
async function load() { const id = String(route.params.id); const [detail, lifecycle, objectTypes] = await Promise.all([assetApi.get(id), assetApi.lifecycle(id), objectApi.types(), loadCatalogs()]); asset.value = detail.data; events.value = lifecycle.data.items; types.value = objectTypes.data.items }
async function completed() { action.value = null; await load() }
onMounted(load)
</script>

<template><section class="page narrow"><RouterLink class="back" to="/assets">← 返回资产台账</RouterLink><div v-if="!asset" class="card empty">正在加载…</div><template v-else>
  <header class="page-header"><div><p class="eyebrow">{{ asset.asset_number }}</p><div class="title-row"><h1>{{ asset.object.name }}</h1><span class="status" :class="asset.lifecycle_status.toLowerCase()">{{ statusName[asset.lifecycle_status] || asset.lifecycle_status }}</span></div><p class="muted">{{ typeName }} · {{ asset.object.model || '型号未记录' }}</p></div><div class="actions"><button v-if="asset.lifecycle_status === 'RECEIVED'" class="button primary" @click="action = 'stock'">办理入库</button><button v-if="asset.lifecycle_status === 'STOCK'" class="button primary" @click="action = 'deploy'">部署到机柜</button><button v-if="['ACTIVE', 'STOCK'].includes(asset.lifecycle_status)" class="button" @click="action = 'transfer'">调拨</button><button v-if="asset.lifecycle_status === 'TRANSFERRED'" class="button primary" @click="action = 'complete-transfer'">完成入库</button><button v-if="['ACTIVE', 'STOCK', 'MAINTENANCE'].includes(asset.lifecycle_status)" class="button" @click="action = 'retire'">退役</button><button v-if="asset.lifecycle_status === 'RETIRED'" class="button" @click="action = 'recover'">退役撤销</button></div></header>
  <div class="asset-detail-grid"><section class="card"><div class="section-title"><h3>基本信息</h3></div><dl class="description-grid single"><div><dt>资产编号</dt><dd>{{ asset.asset_number }}</dd></div><div><dt>供应商</dt><dd>{{ asset.vendor || '—' }}</dd></div><div><dt>到货日期</dt><dd>{{ asset.received_date || '—' }}</dd></div><div><dt>采购成本</dt><dd>{{ asset.cost == null ? '—' : `${asset.currency || 'CNY'} ${asset.cost}` }}</dd></div><div><dt>所有者组织</dt><dd>{{ organizationMap[asset.owner_org_id || ''] || '—' }}</dd></div><div><dt>库存位置</dt><dd>{{ asset.inventory_location?.name || locationMap[asset.inventory_location_id || ''] || '—' }}</dd></div></dl></section>
    <section class="card"><div class="section-title"><h3>关联对象摘要</h3><RouterLink :to="`/objects/${asset.object_id}`">查看对象</RouterLink></div><dl class="description-grid single"><div><dt>对象名称</dt><dd>{{ asset.object.name }}</dd></div><div><dt>对象类型</dt><dd>{{ typeName }}</dd></div><div><dt>序列号</dt><dd>{{ asset.object.serial_number || '—' }}</dd></div><div><dt>型号</dt><dd>{{ asset.object.model || '—' }}</dd></div><div><dt>对象状态</dt><dd>{{ asset.object.status }}</dd></div><div><dt>部署位置</dt><dd>{{ locationMap[asset.object.deployed_location_id || ''] || '—' }}</dd></div></dl></section></div>
  <section class="card lifecycle-card"><div class="section-title"><h3>生命周期时间线</h3><span class="muted">共 {{ events.length }} 个事件</span></div><div v-if="!events.length" class="empty">暂无生命周期事件</div><div v-else class="timeline"><article v-for="(event, index) in events" :key="`${event.event_type}-${index}`" class="timeline-item"><span class="timeline-dot"></span><header><strong>{{ labels[event.event_type] || event.event_type }}</strong><time>{{ date(event.occurred_at) }}</time></header><details v-if="Object.keys(event.details || {}).length"><summary>事件详情</summary><pre>{{ JSON.stringify(event.details, null, 2) }}</pre></details></article></div></section>
  <AssetActionModal v-if="action" :asset="asset" :action="action" @close="action = null" @completed="completed" />
</template></section></template>
