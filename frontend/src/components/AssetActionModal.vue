<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { assetApi } from '../api/assets'
import { rememberOperator, savedOperator } from '../api/inventory'
import { objectApi } from '../api/objects'
import type { Asset, InfrastructureObject, InventoryLocation } from '../types'

const props = defineProps<{ asset: Asset; action: 'stock' | 'deploy' }>()
const emit = defineEmits<{ close: []; completed: [] }>()
const locations = ref<InventoryLocation[]>([])
const racks = ref<InfrastructureObject[]>([])
const targetId = ref('')
const operatorId = ref(savedOperator())
const submitting = ref(false)
const creating = ref(false)
const locationForm = ref({ name: '', warehouse: '', shelf: '', location_code: '', description: '' })

async function createLocation() {
  if (!locationForm.value.name || !locationForm.value.warehouse || !locationForm.value.location_code) return
  const { data } = await assetApi.createLocation({ ...locationForm.value, shelf: locationForm.value.shelf || null, description: locationForm.value.description || null })
  locations.value = (await assetApi.locations()).data.items; targetId.value = data.id; creating.value = false
}
async function submit() {
  if (!targetId.value || !operatorId.value) return
  submitting.value = true
  try {
    rememberOperator(operatorId.value)
    if (props.action === 'stock') await assetApi.stock(props.asset.id, targetId.value, operatorId.value, props.asset.version)
    else await assetApi.deploy(props.asset.id, targetId.value, operatorId.value, props.asset.version)
    emit('completed')
  } finally { submitting.value = false }
}
onMounted(async () => { if (props.action === 'deploy') racks.value = (await objectApi.racks()).data.items; else locations.value = (await assetApi.locations()).data.items })
</script>

<template>
  <div class="modal-mask" @click.self="emit('close')"><section class="modal card" role="dialog" aria-modal="true">
    <header><div><p class="eyebrow">资产 {{ asset.asset_number }}</p><h2>{{ action === 'stock' ? '资产入库' : '部署资产' }}</h2></div><button class="modal-close" aria-label="关闭" @click="emit('close')">×</button></header>
    <template v-if="action === 'stock'">
      <label><span>库存位置</span><select v-model="targetId"><option value="">请选择库存位置</option><option v-for="item in locations" :key="item.id" :value="item.id">{{ item.name }}（{{ item.warehouse }}/{{ item.shelf || item.location_code }}）</option></select></label>
      <p v-if="!locations.length" class="inline-tip">暂无库存位置，请先在此新建位置。</p>
      <button class="link add-location" @click="creating = !creating">{{ creating ? '收起新建表单' : '+ 新建库存位置' }}</button>
      <div v-if="creating" class="inline-form">
        <label><span>位置名称</span><input v-model.trim="locationForm.name" /></label><label><span>仓库</span><input v-model.trim="locationForm.warehouse" /></label>
        <label><span>货架</span><input v-model.trim="locationForm.shelf" /></label><label><span>位置编码</span><input v-model.trim="locationForm.location_code" /></label>
        <button class="button" :disabled="!locationForm.name || !locationForm.warehouse || !locationForm.location_code" @click="createLocation">创建并选择</button>
      </div>
    </template>
    <label v-else><span>目标机柜</span><select v-model="targetId"><option value="">请选择 Rack</option><option v-for="rack in racks" :key="rack.id" :value="rack.id">{{ rack.name }}{{ rack.model ? ` · ${rack.model}` : '' }}</option></select></label>
    <label><span>操作用户 ID</span><input v-model.trim="operatorId" placeholder="后端要求的用户 UUID" /></label>
    <footer><button class="button" @click="emit('close')">取消</button><button class="button primary" :disabled="submitting || !targetId || !operatorId" @click="submit">{{ submitting ? '提交中…' : '确认' }}</button></footer>
  </section></div>
</template>
