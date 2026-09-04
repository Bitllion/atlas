<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { qualityApi } from '../api/quality'
import type { QualityDetailItem, QualityOverviewItem, QualityUnattributedItem } from '../types'

const overviewData = ref<QualityOverviewItem[]>([])
const detailItems = ref<QualityDetailItem[]>([])
const unattributedItems = ref<QualityUnattributedItem[]>([])
const loading = ref(false)
const activeTab = ref<'overview' | 'details' | 'unattributed'>('overview')
const filterType = ref('')
const filterMissing = ref('')
const detailPage = ref(1)
const detailTotal = ref(0)
const unattributedPage = ref(1)
const unattributedTotal = ref(0)
const pageSize = 20

const objectTypes = computed(() => [...new Set(overviewData.value.map(item => item.object_type))])

async function loadOverview() {
  loading.value = true
  try {
    const { data } = await qualityApi.overview()
    overviewData.value = data.by_type
  } finally {
    loading.value = false
  }
}

async function loadDetails() {
  loading.value = true
  try {
    const { data } = await qualityApi.details({
      type: filterType.value || undefined,
      missing: filterMissing.value || undefined,
      page: detailPage.value,
      page_size: pageSize,
    })
    detailItems.value = data.items
    detailTotal.value = data.total
  } finally {
    loading.value = false
  }
}

async function loadUnattributed() {
  loading.value = true
  try {
    const { data } = await qualityApi.unattributed(unattributedPage.value, pageSize)
    unattributedItems.value = data.items
    unattributedTotal.value = data.total
  } finally {
    loading.value = false
  }
}

function switchTab(tab: 'overview' | 'details' | 'unattributed') {
  activeTab.value = tab
  if (tab === 'details' && detailItems.value.length === 0) {
    void loadDetails()
  } else if (tab === 'unattributed' && unattributedItems.value.length === 0) {
    void loadUnattributed()
  }
}

function applyFilter() {
  detailPage.value = 1
  void loadDetails()
}

function nextDetailPage() {
  if (detailPage.value * pageSize < detailTotal.value) {
    detailPage.value++
    void loadDetails()
  }
}

function prevDetailPage() {
  if (detailPage.value > 1) {
    detailPage.value--
    void loadDetails()
  }
}

function nextUnattributedPage() {
  if (unattributedPage.value * pageSize < unattributedTotal.value) {
    unattributedPage.value++
    void loadUnattributed()
  }
}

function prevUnattributedPage() {
  if (unattributedPage.value > 1) {
    unattributedPage.value--
    void loadUnattributed()
  }
}

onMounted(() => {
  void loadOverview()
})
</script>

<template><section class="page arco-page"><header class="page-header"><div><p class="eyebrow">数据治理</p><h1>数据质量中心</h1><p class="muted">基础设施对象数据完整性与质量监控</p></div></header>
<div class="quality-stat-grid"><a-card :bordered="false"><a-statistic title="对象总数" :value="overviewData.reduce((n,i)=>n+i.total,0)"/></a-card><a-card :bordered="false"><a-statistic title="缺少序列号" :value="overviewData.reduce((n,i)=>n+i.missing_serial_number,0)"/></a-card><a-card :bordered="false"><a-statistic title="缺少规格" :value="overviewData.reduce((n,i)=>n+i.missing_spec,0)"/></a-card><a-card :bordered="false"><a-statistic title="低置信度" :value="overviewData.reduce((n,i)=>n+i.low_confidence,0)"/></a-card></div>
<a-card class="quality-tabs-card" :bordered="false"><a-tabs :active-key="activeTab" @change="key=>switchTab(key as 'overview'|'details'|'unattributed')"><a-tab-pane key="overview" title="质量概览"><a-table :data="overviewData" :loading="loading" :pagination="false" row-key="object_type"><template #columns><a-table-column title="对象类型" data-index="object_type"/><a-table-column title="总数" data-index="total"/><a-table-column title="缺序列号" data-index="missing_serial_number"/><a-table-column title="缺厂商" data-index="missing_manufacturer"/><a-table-column title="缺型号" data-index="missing_model"/><a-table-column title="缺规格" data-index="missing_spec"/><a-table-column title="数据陈旧"><template #cell="{record}">{{record.spec_status.stale}}</template></a-table-column><a-table-column title="状态未知"><template #cell="{record}">{{record.spec_status.unknown}}</template></a-table-column><a-table-column title="低置信度" data-index="low_confidence"/></template><template #empty><a-empty description="暂无质量数据"/></template></a-table></a-tab-pane>
<a-tab-pane key="details" title="问题明细"><a-form :model="{}" layout="inline" class="quality-filter" @submit.prevent="applyFilter"><a-form-item label="对象类型"><a-select v-model="filterType" allow-clear placeholder="全部类型"><a-option value="">全部类型</a-option><a-option v-for="item in objectTypes" :key="item" :value="item">{{item}}</a-option></a-select></a-form-item><a-form-item label="缺失字段"><a-select v-model="filterMissing" allow-clear placeholder="全部"><a-option value="">全部</a-option><a-option value="serial_number">缺序列号</a-option><a-option value="manufacturer">缺厂商</a-option><a-option value="model">缺型号</a-option><a-option value="spec">缺规格</a-option></a-select></a-form-item><a-form-item><a-button type="primary" html-type="submit">筛选</a-button></a-form-item></a-form><a-table :data="detailItems" :loading="loading" :pagination="false" row-key="id"><template #columns><a-table-column title="对象名称" data-index="name"/><a-table-column title="对象类型" data-index="object_type"/><a-table-column title="缺失字段"><template #cell="{record}"><a-space wrap><a-tag v-for="field in record.missing_fields" :key="field" color="orange">{{field}}</a-tag><span v-if="!record.missing_fields.length">—</span></a-space></template></a-table-column><a-table-column title="数据状态"><template #cell="{record}">{{record.data_status||'—'}}</template></a-table-column><a-table-column title="置信度"><template #cell="{record}">{{record.confidence||'—'}}</template></a-table-column></template><template #empty><a-empty description="暂无问题数据"/></template></a-table><div class="arco-pagination"><span>共 {{detailTotal}} 条</span><a-button-group><a-button :disabled="detailPage===1" @click="prevDetailPage">上一页</a-button><a-button :disabled="detailPage*pageSize>=detailTotal" @click="nextDetailPage">下一页</a-button></a-button-group></div></a-tab-pane>
<a-tab-pane key="unattributed" title="未归属对象"><a-table :data="unattributedItems" :loading="loading" :pagination="false" row-key="id"><template #columns><a-table-column title="对象名称" data-index="name"/><a-table-column title="对象类型" data-index="object_type"/><a-table-column title="序列号"><template #cell="{record}">{{record.serial_number||'—'}}</template></a-table-column><a-table-column title="厂商"><template #cell="{record}">{{record.manufacturer||'—'}}</template></a-table-column><a-table-column title="型号"><template #cell="{record}">{{record.model||'—'}}</template></a-table-column><a-table-column title="状态"><template #cell="{record}"><a-tag>{{record.status}}</a-tag></template></a-table-column></template><template #empty><a-empty description="暂无未归属对象"/></template></a-table><div class="arco-pagination"><span>共 {{unattributedTotal}} 条</span><a-button-group><a-button :disabled="unattributedPage===1" @click="prevUnattributedPage">上一页</a-button><a-button :disabled="unattributedPage*pageSize>=unattributedTotal" @click="nextUnattributedPage">下一页</a-button></a-button-group></div></a-tab-pane></a-tabs></a-card></section></template>
