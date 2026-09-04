<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { assetApi } from '../api/assets'
import { loadCatalogs } from '../stores/catalog'
import type { InventoryLocation } from '../types'
const locations = ref<InventoryLocation[]>([]); const submitting = ref(false); const loading = ref(false)
const form = ref({ name: '', warehouse: '', shelf: '', location_code: '', description: '' })
async function load() { loading.value=true; try { locations.value=(await assetApi.locations()).data.items } finally { loading.value=false } }
async function create() { submitting.value = true; try { await assetApi.createLocation({ ...form.value, shelf: form.value.shelf || null, description: form.value.description || null }); await Promise.all([load(),loadCatalogs(true)]); form.value = { name: '', warehouse: '', shelf: '', location_code: '', description: '' } } finally { submitting.value = false } }
onMounted(load)
</script>
<template><section class="page narrow"><header class="page-header"><div><p class="eyebrow">INVENTORY</p><h1>库存管理</h1><p class="muted">维护仓库、货架与库存位置编码</p></div><RouterLink class="button" to="/assets">返回资产台账</RouterLink></header>
  <form class="card inventory-form" @submit.prevent="create"><div class="section-title"><h3>新建库存位置</h3></div><div class="form-grid"><label><span>位置名称</span><input v-model.trim="form.name" required /></label><label><span>仓库</span><input v-model.trim="form.warehouse" required /></label><label><span>货架</span><input v-model.trim="form.shelf" /></label><label><span>位置编码</span><input v-model.trim="form.location_code" required /></label></div><label class="wide-field"><span>说明</span><textarea v-model.trim="form.description" rows="2"></textarea></label><div class="form-actions"><button class="button primary" :disabled="submitting" type="submit">{{ submitting ? '创建中…' : '创建位置' }}</button></div></form>
  <section class="card table-card"><div class="section-title"><h3>库存位置</h3><span class="muted">共 {{ locations.length }} 个</span></div><div v-if="loading" class="empty">正在加载…</div><div v-else-if="!locations.length" class="empty">暂无可展示的库存位置</div><table v-else><thead><tr><th>位置名称</th><th>仓库</th><th>货架</th><th>位置编码</th><th>说明</th></tr></thead><tbody><tr v-for="item in locations" :key="item.id"><td class="name-cell">{{ item.name }}</td><td>{{ item.warehouse }}</td><td>{{ item.shelf || '—' }}</td><td>{{ item.location_code }}</td><td>{{ item.description || '—' }}</td></tr></tbody></table></section>
</section></template>
