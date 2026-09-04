<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { IconArchive, IconSearch } from '@arco-design/web-vue/es/icon'
import { assetApi } from '../api/assets'
import AssetActionModal from '../components/AssetActionModal.vue'
import { loadCatalogs, useCatalog } from '../stores/catalog'
import type { Asset } from '../types'
const router = useRouter()
type AssetAction = 'stock' | 'deploy' | 'transfer' | 'complete-transfer' | 'retire' | 'recover'
const assets = ref<Asset[]>([]), loading = ref(false), total = ref(0), page = ref(1), status = ref('')
const action = ref<AssetAction | null>(null), selected = ref<Asset | null>(null)
const { organizationMap, locationMap, objectTypeMap } = useCatalog(); const pageSize = 20
const statusName: Record<string, string> = { REQUESTED: '已申请', APPROVED: '已批准', ORDERED: '已下单', PURCHASED: '已采购', RECEIVED: '已到货', STOCK: '库存中', IN_TRANSIT: '运输中', DEPLOYING: '部署中', DEPLOYED: '已部署', ACTIVE: '使用中', MAINTENANCE: '维护中', TRANSFERRED: '调拨中', RETIRED: '已退役', RECOVERED: '已撤销' }
const statusColor = (value: string) => ({ REQUESTED: 'blue', APPROVED: 'arcoblue', ORDERED: 'purple', PURCHASED: 'cyan', RECEIVED: 'orange', STOCK: 'green', IN_TRANSIT: 'gold', DEPLOYING: 'orange', DEPLOYED: 'lime', ACTIVE: 'green', MAINTENANCE: 'orangered', TRANSFERRED: 'purple', RETIRED: 'gray', RECOVERED: 'blue' }[value] || 'gray')
async function load() { loading.value = true; try { const { data } = await assetApi.list({ status: status.value || undefined, page: page.value, page_size: pageSize }); assets.value = data.items; total.value = data.total } finally { loading.value = false } }
function filter() { page.value = 1; void load() }
function open(item: Asset, kind: AssetAction) { selected.value = item; action.value = kind }
async function completed() { action.value = null; selected.value = null; await load() }
onMounted(async () => { await Promise.all([loadCatalogs(), load()]) })
</script>
<template><section class="page arco-page">
  <header class="page-header"><div><p class="eyebrow">资产生命周期</p><h1>资产台账</h1><p class="muted">管理资产从到货、入库到部署使用的完整生命周期</p></div><a-button @click="router.push('/inventory')"><template #icon><IconArchive /></template>库存位置</a-button></header>
  <a-card class="arco-filter-card" :bordered="false"><a-form :model="{}" layout="inline" @submit.prevent="filter"><a-form-item label="生命周期状态"><a-select v-model="status" placeholder="全部状态" allow-clear><a-option value="">全部状态</a-option><a-option v-for="(name, value) in statusName" :key="value" :value="value">{{ name }}</a-option></a-select></a-form-item><a-form-item><a-button type="primary" html-type="submit"><template #icon><IconSearch /></template>查询</a-button></a-form-item></a-form></a-card>
  <a-card class="arco-table-card" :bordered="false"><a-table :data="assets" :loading="loading" :pagination="false" row-key="id" :scroll="{ x: 1200 }" @row-click="(item) => router.push(`/assets/${(item as Asset).id}`)"><template #columns>
    <a-table-column title="资产编号" data-index="asset_number" :width="160"><template #cell="{ record }"><a-link class="object-name">{{ record.asset_number }}</a-link></template></a-table-column><a-table-column title="设备" :width="180"><template #cell="{ record }">{{ record.object.name }}</template></a-table-column><a-table-column title="类型" :width="130"><template #cell="{ record }">{{ objectTypeMap[record.object.object_type_id] || '—' }}</template></a-table-column><a-table-column title="状态" :width="110"><template #cell="{ record }"><a-tag :color="statusColor(record.lifecycle_status)" bordered>{{ statusName[record.lifecycle_status] || record.lifecycle_status }}</a-tag></template></a-table-column><a-table-column title="所有者" :width="150"><template #cell="{ record }">{{ organizationMap[record.owner_org_id || ''] || '—' }}</template></a-table-column><a-table-column title="位置" :width="160"><template #cell="{ record }">{{ locationMap[record.inventory_location_id || record.object.deployed_location_id || ''] || '—' }}</template></a-table-column>
    <a-table-column title="操作" fixed="right" :width="290"><template #cell="{ record }"><div class="table-actions" @click.stop><a-button v-if="record.lifecycle_status === 'RECEIVED'" type="text" size="small" @click="open(record, 'stock')">入库</a-button><a-button v-if="record.lifecycle_status === 'STOCK'" type="text" size="small" @click="open(record, 'deploy')">部署</a-button><a-button v-if="['ACTIVE', 'STOCK'].includes(record.lifecycle_status)" type="text" size="small" @click="open(record, 'transfer')">调拨</a-button><a-button v-if="record.lifecycle_status === 'TRANSFERRED'" type="text" size="small" @click="open(record, 'complete-transfer')">完成入库</a-button><a-button v-if="['ACTIVE', 'STOCK', 'MAINTENANCE'].includes(record.lifecycle_status)" type="text" status="danger" size="small" @click="open(record, 'retire')">退役</a-button><a-button v-if="record.lifecycle_status === 'RETIRED'" type="text" size="small" @click="open(record, 'recover')">退役撤销</a-button><a-button type="text" size="small" @click="router.push(`/assets/${record.id}`)">详情</a-button></div></template></a-table-column>
  </template><template #empty><a-empty description="暂无资产记录" /></template></a-table><div class="arco-pagination"><span>共 {{ total }} 条</span><a-pagination :current="page" :page-size="pageSize" :total="total" :show-total="false" @change="(value) => { page = value; load() }" /></div></a-card>
  <AssetActionModal v-if="selected && action" :asset="selected" :action="action" @close="action = null; selected = null" @completed="completed" />
</section></template>
