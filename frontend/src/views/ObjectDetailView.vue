<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { objectApi } from '../api/objects'
import type { InfrastructureObject, ObjectDetail, ObjectHistory, Relationship, RelationshipType } from '../types'

const route = useRoute(); const id = route.params.id as string
const object = ref<ObjectDetail>(); const histories = ref<ObjectHistory[]>([]); const relations = ref<Relationship[]>([])
const objectNames = ref<Record<string, string>>({}); const relationTypes = ref<Record<string, RelationshipType>>({}); const activeTab = ref('basic'); const loading = ref(true)
const info = computed(() => object.value ? [
  ['名称', object.value.name], ['对象类型', object.value.object_type.display_name || object.value.object_type.name], ['状态', object.value.status], ['制造商', object.value.manufacturer], ['型号', object.value.model], ['序列号', object.value.serial_number], ['资产编号', object.value.asset_number], ['固件版本', object.value.firmware_version], ['所有权', object.value.ownership], ['管理范围', object.value.management_scope], ['所有者组织', object.value.owner_org_id], ['部署位置', object.value.deployed_location_id], ['更新时间', new Date(object.value.updated_at).toLocaleString('zh-CN')]
] : [])
function display(value: unknown) { if (value == null || value === '') return '—'; return typeof value === 'object' ? JSON.stringify(value) : String(value) }
function changedFields(item: ObjectHistory) {
  const before = item.before_data || {}; const after = item.after_data || {}
  return Array.from(new Set([...Object.keys(before), ...Object.keys(after)])).filter((key) => JSON.stringify(before[key]) !== JSON.stringify(after[key]))
}
function relationLabel(item: Relationship) { return relationTypes.value[item.relationship_type_id]?.display_name || relationTypes.value[item.relationship_type_id]?.name || '关联' }
function objectName(objectId: string) { return objectId === id ? object.value?.name || objectId : objectNames.value[objectId] || objectId }
onMounted(async () => {
  try {
    const [detail, history, outgoing, incoming, typeResponse, allObjects] = await Promise.all([objectApi.get(id), objectApi.history(id), objectApi.relations({ source_object_id: id }), objectApi.relations({ target_object_id: id }), objectApi.relationshipTypes(), objectApi.list({ page: 1, page_size: 200 })])
    object.value = detail.data; histories.value = history.data.items
    relations.value = [...outgoing.data.items, ...incoming.data.items.filter((item) => !outgoing.data.items.some((other) => other.id === item.id))]
    relationTypes.value = Object.fromEntries(typeResponse.data.items.map((item) => [item.id, item])); objectNames.value = Object.fromEntries(allObjects.data.items.map((item: InfrastructureObject) => [item.id, item.name]))
  } finally { loading.value = false }
})
</script>

<template><section class="page"><div v-if="loading" class="card empty">正在加载…</div><template v-else-if="object">
  <header class="page-header"><div><RouterLink class="back" to="/objects">← 返回对象列表</RouterLink><div class="title-row"><h1>{{ object.name }}</h1><span class="status" :class="object.status.toLowerCase()">{{ object.status }}</span></div><p class="muted">{{ object.object_type.display_name || object.object_type.name }} · {{ object.manufacturer || '未知制造商' }} {{ object.model || '' }}</p></div><RouterLink class="button primary" :to="`/objects/${id}/edit`">编辑对象</RouterLink></header>
  <div class="summary-grid"><div class="summary-card"><strong>{{ object.relationship_summary.total }}</strong><span>关联关系</span></div><div class="summary-card"><strong>{{ Object.keys(object.spec_data).length }}</strong><span>规格字段</span></div><div class="summary-card"><strong>v{{ object.version }}</strong><span>数据版本</span></div></div>
  <div class="card detail-card"><nav class="tabs"><button :class="{ active: activeTab === 'basic' }" @click="activeTab='basic'">基础信息</button><button :class="{ active: activeTab === 'spec' }" @click="activeTab='spec'">Specification</button><button :class="{ active: activeTab === 'relations' }" @click="activeTab='relations'">Relationships <span class="count">{{ relations.length }}</span></button><button :class="{ active: activeTab === 'history' }" @click="activeTab='history'">History <span class="count">{{ histories.length }}</span></button></nav>
    <div v-if="activeTab === 'basic'" class="description-grid"><div v-for="([label, value]) in info" :key="String(label)"><dt>{{ label }}</dt><dd>{{ display(value) }}</dd></div></div>
    <div v-else-if="activeTab === 'spec'"><div v-if="!Object.keys(object.spec_data).length" class="empty">暂无规格数据</div><div v-else class="spec-list"><div v-for="(value, key) in object.spec_data" :key="key"><code>{{ key }}</code><span>{{ display(value) }}</span></div></div></div>
    <div v-else-if="activeTab === 'relations'"><div v-if="!relations.length" class="empty">暂无关联关系</div><div v-else class="relation-list"><div v-for="item in relations" :key="item.id" class="relation-row"><RouterLink :to="`/objects/${item.source_object_id}`">{{ objectName(item.source_object_id) }}</RouterLink><span class="relation-arrow">— {{ relationLabel(item) }} →</span><RouterLink :to="`/objects/${item.target_object_id}`">{{ objectName(item.target_object_id) }}</RouterLink><span class="muted">{{ item.confidence }} · {{ item.data_source }}</span></div></div></div>
    <div v-else class="timeline"><div v-if="!histories.length" class="empty">暂无历史记录</div><article v-for="item in histories" :key="item.id" class="timeline-item"><span class="timeline-dot"></span><header><strong>{{ item.change_type }}</strong><time>{{ new Date(item.created_at).toLocaleString('zh-CN') }}</time></header><p>来源：{{ item.source }}<template v-if="item.operator"> · 操作人：{{ item.operator }}</template></p><details v-if="changedFields(item).length"><summary>查看变更（{{ changedFields(item).length }} 项）</summary><div v-for="field in changedFields(item)" :key="field" class="change"><code>{{ field }}</code><span>{{ display(item.before_data?.[field]) }}</span><b>→</b><span>{{ display(item.after_data?.[field]) }}</span></div></details></article></div>
  </div></template></section></template>
