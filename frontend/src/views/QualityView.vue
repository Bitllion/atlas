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

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">DATA QUALITY</p>
        <h1>数据质量中心</h1>
        <p class="muted">基础设施对象数据完整性与质量监控</p>
      </div>
    </header>

    <div class="card">
      <div class="tabs">
        <button :class="{ active: activeTab === 'overview' }" @click="switchTab('overview')">
          质量概览
        </button>
        <button :class="{ active: activeTab === 'details' }" @click="switchTab('details')">
          问题明细
        </button>
        <button :class="{ active: activeTab === 'unattributed' }" @click="switchTab('unattributed')">
          未归属对象
        </button>
      </div>

      <!-- 质量概览 -->
      <div v-if="activeTab === 'overview'">
        <div v-if="loading" class="empty">正在加载…</div>
        <div v-else-if="overviewData.length === 0" class="empty">暂无数据</div>
        <div v-else class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>对象类型</th>
                <th>总数</th>
                <th>缺 SN</th>
                <th>缺厂商</th>
                <th>缺型号</th>
                <th>缺规格</th>
                <th>STALE</th>
                <th>UNKNOWN</th>
                <th>低置信度</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in overviewData" :key="item.object_type">
                <td class="name-cell">{{ item.object_type }}</td>
                <td>{{ item.total }}</td>
                <td>{{ item.missing_serial_number }}</td>
                <td>{{ item.missing_manufacturer }}</td>
                <td>{{ item.missing_model }}</td>
                <td>{{ item.missing_spec }}</td>
                <td>{{ item.spec_status.stale }}</td>
                <td>{{ item.spec_status.unknown }}</td>
                <td>{{ item.low_confidence }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 问题明细 -->
      <div v-if="activeTab === 'details'">
        <div class="filter-bar compact-filter">
          <label>
            <span>对象类型</span>
            <select v-model="filterType">
              <option value="">全部类型</option>
              <option v-for="type in objectTypes" :key="type" :value="type">{{ type }}</option>
            </select>
          </label>
          <label>
            <span>缺失字段</span>
            <select v-model="filterMissing">
              <option value="">全部</option>
              <option value="serial_number">缺 SN</option>
              <option value="manufacturer">缺厂商</option>
              <option value="model">缺型号</option>
              <option value="spec">缺规格</option>
            </select>
          </label>
          <button class="button primary" @click="applyFilter">筛选</button>
        </div>

        <div v-if="loading" class="empty">正在加载…</div>
        <div v-else-if="detailItems.length === 0" class="empty">暂无问题数据</div>
        <div v-else>
          <div class="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>对象名称</th>
                  <th>对象类型</th>
                  <th>缺失字段</th>
                  <th>数据状态</th>
                  <th>置信度</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in detailItems" :key="item.id">
                  <td class="name-cell">{{ item.name }}</td>
                  <td>{{ item.object_type }}</td>
                  <td>{{ item.missing_fields.join(', ') || '—' }}</td>
                  <td>{{ item.data_status || '—' }}</td>
                  <td>{{ item.confidence || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="pagination">
            <div>显示 {{ (detailPage - 1) * pageSize + 1 }} - {{ Math.min(detailPage * pageSize, detailTotal) }} / 共 {{ detailTotal }} 条</div>
            <div>
              <button :disabled="detailPage === 1" @click="prevDetailPage">上一页</button>
              <button :disabled="detailPage * pageSize >= detailTotal" @click="nextDetailPage">下一页</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 未归属对象 -->
      <div v-if="activeTab === 'unattributed'">
        <div v-if="loading" class="empty">正在加载…</div>
        <div v-else-if="unattributedItems.length === 0" class="empty">暂无未归属对象</div>
        <div v-else>
          <div class="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>对象名称</th>
                  <th>对象类型</th>
                  <th>序列号</th>
                  <th>厂商</th>
                  <th>型号</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in unattributedItems" :key="item.id">
                  <td class="name-cell">{{ item.name }}</td>
                  <td>{{ item.object_type }}</td>
                  <td>{{ item.serial_number || '—' }}</td>
                  <td>{{ item.manufacturer || '—' }}</td>
                  <td>{{ item.model || '—' }}</td>
                  <td><span class="status" :class="item.status.toLowerCase()">{{ item.status }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="pagination">
            <div>显示 {{ (unattributedPage - 1) * pageSize + 1 }} - {{ Math.min(unattributedPage * pageSize, unattributedTotal) }} / 共 {{ unattributedTotal }} 条</div>
            <div>
              <button :disabled="unattributedPage === 1" @click="prevUnattributedPage">上一页</button>
              <button :disabled="unattributedPage * pageSize >= unattributedTotal" @click="nextUnattributedPage">下一页</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
