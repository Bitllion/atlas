<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { IconApps, IconArchive, IconCheckCircle, IconClockCircle, IconTool } from '@arco-design/web-vue/es/icon'
import { dashboardApi } from '../api/dashboard'
import type { DashboardAssets, DashboardOverview, OperationsSummary } from '../types'

const overview = ref<DashboardOverview | null>(null), assets = ref<DashboardAssets | null>(null), operations = ref<OperationsSummary | null>(null), loading = ref(true)
const maxDevice = computed(() => Math.max(1, ...(overview.value?.devices.by_type.map((item) => item.count) || [1])))
const maxAsset = computed(() => Math.max(1, ...(assets.value?.by_status.map((item) => item.count) || [1])))
const statusName: Record<string, string> = { REQUESTED: '已申请', APPROVED: '已批准', ORDERED: '已下单', PURCHASED: '已采购', RECEIVED: '已接收', STOCK: '库存中', IN_TRANSIT: '运输中', DEPLOYING: '部署中', DEPLOYED: '已部署', ACTIVE: '使用中', MAINTENANCE: '维护中', TRANSFERRED: '已调拨', RETIRED: '已退役', RECOVERED: '已回收', CREATED: '已创建', ASSIGNED: '已分配', PROCESSING: '处理中', WAITING: '等待中', SUSPENDED: '已暂停', RESOLVED: '已解决', CLOSED: '已关闭', CANCELLED: '已取消', REOPENED: '已重开' }
const metrics = computed(() => [
  { title: '设备总数', value: overview.value?.devices.total || 0, suffix: '基础设施对象', icon: IconApps, tone: 'blue' },
  { title: '资产总数', value: assets.value?.total || 0, suffix: '资产记录', icon: IconArchive, tone: 'cyan' },
  { title: '待处理工单', value: operations.value?.open || 0, suffix: `共 ${operations.value?.total || 0} 张`, icon: IconTool, tone: 'orange' },
  { title: '本月新增工单', value: operations.value?.new_this_month || 0, suffix: `已解决 ${operations.value?.resolved || 0} 张`, icon: IconCheckCircle, tone: 'green' },
  { title: '平均修复时间', value: operations.value?.average_repair_hours || 0, suffix: '小时', icon: IconClockCircle, tone: 'purple' },
])
onMounted(async () => { try { const [o, a, p] = await Promise.all([dashboardApi.overview(), dashboardApi.assets(), dashboardApi.operations()]); overview.value = o.data; assets.value = a.data; operations.value = p.data } finally { loading.value = false } })
</script>

<template>
  <section class="page arco-page">
    <header class="page-header"><div><p class="eyebrow">运营总览</p><h1>工作台</h1><p class="muted">基础设施资产与运维运营总览</p></div></header>
    <a-spin :loading="loading" tip="正在加载运营数据…" class="dashboard-spin">
      <div class="arco-metric-grid">
        <a-card v-for="item in metrics" :key="item.title" class="arco-metric-card" :bordered="false">
          <div class="metric-heading"><span>{{ item.title }}</span><span class="metric-icon" :class="item.tone"><component :is="item.icon" /></span></div>
          <a-statistic :value="item.value" :value-style="{ color: '#1d2129', fontSize: '28px', fontWeight: 600 }" />
          <small>{{ item.suffix }}</small>
        </a-card>
      </div>
      <div class="arco-dashboard-grid">
        <a-card title="设备类型分布" :bordered="false"><template #extra><span class="muted">共 {{ overview?.devices.total || 0 }} 个</span></template><a-empty v-if="!overview?.devices.by_type.length" description="暂无设备数据" /><div v-else class="distribution-list"><div v-for="item in overview.devices.by_type" :key="item.type"><span>{{ item.type }}</span><a-progress :percent="item.count / maxDevice" :show-text="false" /><strong>{{ item.count }}</strong></div></div></a-card>
        <a-card title="资产状态分布" :bordered="false"><template #extra><span class="muted">生命周期状态</span></template><a-empty v-if="!assets?.by_status.length" description="暂无资产数据" /><div v-else class="distribution-list asset-distribution"><div v-for="item in assets.by_status" :key="item.status"><span>{{ statusName[item.status || ''] || item.status }}</span><a-progress :percent="item.count / maxAsset" :show-text="false" status="success" /><strong>{{ item.count }}</strong></div></div></a-card>
        <a-card title="工单状态" :bordered="false" class="workorder-distribution"><template #extra><span class="muted">实时统计</span></template><a-empty v-if="!operations?.by_status?.length" description="暂无工单数据" /><div v-else class="status-statistics"><div v-for="item in operations.by_status" :key="item.status"><a-statistic :value="item.count" /><span>{{ statusName[item.status || ''] || item.status }}</span></div></div></a-card>
      </div>
    </a-spin>
  </section>
</template>
