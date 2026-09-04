<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { IconArchive, IconBook, IconRight, IconSearch, IconTool } from '@arco-design/web-vue/es/icon'
import { dashboardApi } from '../api/dashboard'
import type { SearchItem } from '../types'
const route = useRoute(), router = useRouter(), items = ref<SearchItem[]>([]), total = ref(0), loading = ref(false), page = ref(1), pageSize = 20
const query = computed(() => String(route.query.q || '').trim())
const groups = computed(() => ['object', 'asset', 'work_order', 'knowledge_article'].map(type => ({ type, items: items.value.filter(item => item.resource_type === type) })).filter(group => group.items.length))
const labels: Record<string, string> = { object: '基础设施对象', asset: '资产', work_order: '运维工单', knowledge_article: '知识文章' }
const icons: Record<string, unknown> = { object: IconSearch, asset: IconArchive, work_order: IconTool, knowledge_article: IconBook }
function path(item: SearchItem) { return { object: `/objects/${item.id}`, asset: `/assets/${item.id}`, work_order: `/work-orders/${item.id}`, knowledge_article: `/knowledge/${item.id}` }[item.resource_type] }
async function load() { if (!query.value) { items.value = []; total.value = 0; return } loading.value = true; try { const { data } = await dashboardApi.search(query.value, page.value, pageSize); items.value = data.items; total.value = data.total } finally { loading.value = false } }
function change(value: number) { page.value = value; void load() }
watch(query, () => { page.value = 1; void load() }, { immediate: true })
</script>
<template><section class="page narrow arco-page"><header class="page-header"><div><p class="eyebrow">全局搜索</p><h1>搜索结果</h1><p class="muted"><template v-if="query">“{{ query }}” 共找到 {{ total }} 条结果</template><template v-else>搜索对象、资产、运维工单与知识文章</template></p></div></header>
<a-spin :loading="loading" tip="正在搜索…" class="search-spin"><a-empty v-if="!query" description="请在顶部搜索框输入关键词" /><a-empty v-else-if="!items.length && !loading" description="未找到相关对象、资产、工单或知识文章" /><div v-else class="arco-search-groups"><a-card v-for="group in groups" :key="group.type" class="arco-search-card" :bordered="false"><template #title><a-space><component :is="icons[group.type]" /><span>{{ labels[group.type] }}</span><a-tag color="arcoblue">{{ group.items.length }}</a-tag></a-space></template><a-list :bordered="false"><a-list-item v-for="result in group.items" :key="result.id" class="arco-search-result" action-layout="vertical" @click="router.push(path(result))"><a-list-item-meta :title="result.name" :description="result.summary || '暂无摘要'" /><template #actions><a-link>查看详情 <IconRight /></a-link></template></a-list-item></a-list></a-card></div></a-spin>
<div v-if="total > pageSize" class="search-pagination"><span>共 {{ total }} 条</span><a-pagination :current="page" :page-size="pageSize" :total="total" @change="change" /></div></section></template>
