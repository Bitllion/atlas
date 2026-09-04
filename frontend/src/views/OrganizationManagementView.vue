<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { adminApi } from '../api/admin'
import { loadCatalogs } from '../stores/catalog'
import type { Organization, OrganizationType } from '../types'

const items=ref<Organization[]>([]),total=ref(0),page=ref(1),search=ref(''),loading=ref(false),saving=ref(false),modal=ref(false),editing=ref<Organization|null>(null)
const pageSize=20,totalPages=computed(()=>Math.max(1,Math.ceil(total.value/pageSize)))
const form=reactive({name:'',org_type:'INTERNAL' as OrganizationType,is_active:true})
const typeName:Record<OrganizationType,string>={INTERNAL:'内部组织',CUSTOMER:'客户',VENDOR:'供应商'}
async function load(){loading.value=true;try{const {data}=await adminApi.organizations({search:search.value||undefined,page:page.value,page_size:pageSize});items.value=data.items;total.value=data.total}finally{loading.value=false}}
function query(){page.value=1;void load()}
function openCreate(){editing.value=null;Object.assign(form,{name:'',org_type:'INTERNAL',is_active:true});modal.value=true}
function openEdit(item:Organization){editing.value=item;Object.assign(form,{name:item.name,org_type:item.org_type,is_active:item.is_active});modal.value=true}
async function save(){saving.value=true;try{if(editing.value)await adminApi.updateOrganization(editing.value.id,{name:form.name,is_active:form.is_active});else await adminApi.createOrganization({name:form.name,org_type:form.org_type});modal.value=false;await Promise.all([load(),loadCatalogs(true)])}finally{saving.value=false}}
onMounted(load)
</script>
<template><section class="page"><header class="page-header"><div><p class="eyebrow">SYSTEM MANAGEMENT</p><h1>组织管理</h1><p class="muted">维护内部组织、客户与供应商信息</p></div><button class="button primary" @click="openCreate">+ 新建组织</button></header>
<form class="filter-bar card compact-filter" @submit.prevent="query"><label><span>组织名称</span><input v-model.trim="search" placeholder="输入关键字" /></label><button class="button">查询</button></form>
<div class="card table-card"><div v-if="loading" class="empty">正在加载…</div><div v-else-if="!items.length" class="empty">暂无组织</div><div v-else class="table-scroll"><table><thead><tr><th>组织名称</th><th>组织类型</th><th>状态</th><th>更新时间</th><th>操作</th></tr></thead><tbody><tr v-for="item in items" :key="item.id"><td class="name-cell">{{item.name}}</td><td>{{typeName[item.org_type]}}</td><td><span class="status" :class="item.is_active?'active':'inactive'">{{item.is_active?'已启用':'已停用'}}</span></td><td>{{new Date(item.updated_at).toLocaleString('zh-CN')}}</td><td><button class="link" @click="openEdit(item)">编辑</button></td></tr></tbody></table></div><footer class="pagination"><span>共 {{total}} 条</span><div><button :disabled="page<=1" @click="page--;load()">上一页</button><span>第 {{page}} / {{totalPages}} 页</span><button :disabled="page>=totalPages" @click="page++;load()">下一页</button></div></footer></div>
<div v-if="modal" class="modal-mask" @click.self="modal=false"><form class="modal card" @submit.prevent="save"><header><div><p class="eyebrow">{{editing?'EDIT':'CREATE'}} ORGANIZATION</p><h2>{{editing?'编辑组织':'新建组织'}}</h2></div><button class="modal-close" type="button" @click="modal=false">×</button></header><label><span>组织名称 *</span><input v-model.trim="form.name" required maxlength="255" /></label><label><span>组织类型 *</span><select v-model="form.org_type" required :disabled="!!editing"><option value="INTERNAL">内部组织</option><option value="CUSTOMER">客户</option><option value="VENDOR">供应商</option></select><small v-if="editing" class="muted">当前后端契约不支持修改组织类型</small></label><label v-if="editing" class="checkbox-field"><input v-model="form.is_active" type="checkbox" /><span>启用组织</span></label><footer><button class="button" type="button" @click="modal=false">取消</button><button class="button primary" :disabled="saving">{{saving?'保存中…':'保存'}}</button></footer></form></div>
</section></template>
