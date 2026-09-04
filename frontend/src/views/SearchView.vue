<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { dashboardApi } from '../api/dashboard'
import type { SearchItem } from '../types'
const route=useRoute(),router=useRouter(),items=ref<SearchItem[]>([]),total=ref(0),loading=ref(false),page=ref(1),pageSize=20
const query=computed(()=>String(route.query.q||'').trim()), totalPages=computed(()=>Math.max(1,Math.ceil(total.value/pageSize)))
const groups=computed(()=>['object','asset','work_order','knowledge_article'].map(type=>({type,items:items.value.filter(item=>item.resource_type===type)})).filter(group=>group.items.length))
const labels:Record<string,string>={object:'基础设施对象',asset:'资产',work_order:'运维工单',knowledge_article:'知识文章'}
function path(item:SearchItem){return {object:`/objects/${item.id}`,asset:`/assets/${item.id}`,work_order:`/work-orders/${item.id}`,knowledge_article:`/knowledge/${item.id}`}[item.resource_type]}
async function load(){if(!query.value){items.value=[];total.value=0;return}loading.value=true;try{const {data}=await dashboardApi.search(query.value,page.value,pageSize);items.value=data.items;total.value=data.total}finally{loading.value=false}}
function change(value:number){page.value=value;void load()}
watch(query,()=>{page.value=1;void load()},{immediate:true})
</script>
<template><section class="page narrow"><header class="page-header"><div><p class="eyebrow">GLOBAL SEARCH</p><h1>全局搜索</h1><p class="muted">“{{query}}” 的搜索结果，共 {{total}} 条</p></div></header><div v-if="loading" class="card empty">正在搜索…</div><div v-else-if="!query" class="card empty">请在左侧搜索框输入关键词</div><div v-else-if="!items.length" class="card empty">未找到相关对象、资产、工单或知识文章</div><div v-else class="search-groups"><section v-for="group in groups" :key="group.type" class="card search-group"><div class="section-title"><h3>{{labels[group.type]}}</h3><span class="count">{{group.items.length}}</span></div><button v-for="item in group.items" :key="item.id" class="search-result" @click="router.push(path(item))"><strong>{{item.name}}</strong><span>{{item.summary||'暂无摘要'}}</span><b>查看 ›</b></button></section></div><footer v-if="total>pageSize" class="pagination"><span>共 {{total}} 条</span><div><button :disabled="page<=1" @click="change(page-1)">上一页</button><span>第 {{page}} / {{totalPages}} 页</span><button :disabled="page>=totalPages" @click="change(page+1)">下一页</button></div></footer></section></template>
