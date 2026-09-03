<script setup lang="ts">
import { ref } from 'vue'
import { assetApi } from '../api/assets'
import { rememberLocation, savedLocations } from '../api/inventory'
import type { InventoryLocation } from '../types'
const locations = ref<InventoryLocation[]>(savedLocations()); const submitting = ref(false)
const form = ref({ name: '', warehouse: '', shelf: '', location_code: '', description: '' })
async function create() { submitting.value = true; try { const { data } = await assetApi.createLocation({ ...form.value, shelf: form.value.shelf || null, description: form.value.description || null }); rememberLocation(data); locations.value = savedLocations(); form.value = { name: '', warehouse: '', shelf: '', location_code: '', description: '' } } finally { submitting.value = false } }
</script>
<template><section class="page narrow"><header class="page-header"><div><p class="eyebrow">INVENTORY</p><h1>库存管理</h1><p class="muted">维护仓库、货架与库存位置编码</p></div><RouterLink class="button" to="/assets">返回资产台账</RouterLink></header>
  <form class="card inventory-form" @submit.prevent="create"><div class="section-title"><h3>新建库存位置</h3></div><div class="form-grid"><label><span>位置名称</span><input v-model.trim="form.name" required /></label><label><span>仓库</span><input v-model.trim="form.warehouse" required /></label><label><span>货架</span><input v-model.trim="form.shelf" /></label><label><span>位置编码</span><input v-model.trim="form.location_code" required /></label></div><label class="wide-field"><span>说明</span><textarea v-model.trim="form.description" rows="2"></textarea></label><div class="form-actions"><button class="button primary" :disabled="submitting" type="submit">{{ submitting ? '创建中…' : '创建位置' }}</button></div></form>
  <section class="card table-card"><div class="section-title"><h3>库存位置</h3><span class="muted">当前浏览器已创建 {{ locations.length }} 个</span></div><p class="contract-note">后端 Phase 3a 尚未提供库存位置查询接口，当前列表仅展示本浏览器通过 Atlas 新建的位置。</p><div v-if="!locations.length" class="empty">暂无可展示的库存位置</div><table v-else><thead><tr><th>位置名称</th><th>仓库</th><th>货架</th><th>位置编码</th><th>说明</th></tr></thead><tbody><tr v-for="item in locations" :key="item.id"><td class="name-cell">{{ item.name }}</td><td>{{ item.warehouse }}</td><td>{{ item.shelf || '—' }}</td><td>{{ item.location_code }}</td><td>{{ item.description || '—' }}</td></tr></tbody></table></section>
</section></template>
