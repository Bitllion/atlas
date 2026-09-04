<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { assetApi } from '../api/assets'
import { rememberOperator, savedOperator } from '../api/inventory'
import { objectApi } from '../api/objects'
import type { Asset, InfrastructureObject, InventoryLocation, Organization } from '../types'

type AssetAction = 'stock' | 'deploy' | 'transfer' | 'complete-transfer' | 'retire' | 'recover'
const props = defineProps<{ asset: Asset; action: AssetAction }>()
const emit = defineEmits<{ close: []; completed: [] }>()
const locations = ref<InventoryLocation[]>([])
const racks = ref<InfrastructureObject[]>([])
const organizations = ref<Organization[]>([])
const targetId = ref('')
const notes = ref('')
const reason = ref('')
const disposition = ref<'RMA' | 'SCRAPPED' | 'RETURNED_TO_VENDOR'>('SCRAPPED')
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
  if ((['stock', 'deploy', 'transfer', 'complete-transfer'].includes(props.action) && !targetId.value) || (['stock', 'deploy'].includes(props.action) && !operatorId.value) || (['retire', 'recover'].includes(props.action) && !reason.value.trim())) return
  submitting.value = true
  try {
    rememberOperator(operatorId.value)
    if (props.action === 'stock') await assetApi.stock(props.asset.id, targetId.value, operatorId.value, props.asset.version)
    else if (props.action === 'deploy') await assetApi.deploy(props.asset.id, targetId.value, operatorId.value, props.asset.version)
    else if (props.action === 'transfer') await assetApi.transfer(props.asset.id, targetId.value, notes.value.trim(), props.asset.version)
    else if (props.action === 'complete-transfer') await assetApi.completeTransfer(props.asset.id, targetId.value, props.asset.version)
    else if (props.action === 'retire') await assetApi.retire(props.asset.id, reason.value.trim(), disposition.value, props.asset.version)
    else await assetApi.recover(props.asset.id, reason.value.trim(), props.asset.version)
    emit('completed')
  } finally { submitting.value = false }
}
onMounted(async () => {
  if (props.action === 'deploy') racks.value = (await objectApi.racks()).data.items
  else if (props.action === 'stock' || props.action === 'complete-transfer') locations.value = (await assetApi.locations()).data.items
  else if (props.action === 'transfer') {
    const { adminApi } = await import('../api/admin')
    organizations.value = (await adminApi.organizations({ page: 1, page_size: 200 })).data.items
  }
})

const titles: Record<AssetAction, string> = { stock: '资产入库', deploy: '部署资产', transfer: '资产调拨', 'complete-transfer': '完成入库', retire: '资产退役', recover: '退役撤销' }
const canSubmit = () => {
  if (props.action === 'retire' || props.action === 'recover') return Boolean(reason.value.trim())
  if (props.action === 'stock' || props.action === 'deploy') return Boolean(targetId.value && operatorId.value)
  return Boolean(targetId.value)
}
</script>

<template>
  <div class="modal-mask" @click.self="emit('close')"><section class="modal card" role="dialog" aria-modal="true">
    <header><div><p class="eyebrow">资产 {{ asset.asset_number }}</p><h2>{{ titles[action] }}</h2></div><button class="modal-close" aria-label="关闭" @click="emit('close')">×</button></header>
    <template v-if="action === 'stock' || action === 'complete-transfer'">
      <label><span>库存位置</span><select v-model="targetId"><option value="">请选择库存位置</option><option v-for="item in locations" :key="item.id" :value="item.id">{{ item.name }}（{{ item.warehouse }}/{{ item.shelf || item.location_code }}）</option></select></label>
      <p v-if="!locations.length" class="inline-tip">暂无库存位置，请先在此新建位置。</p>
      <button v-if="action === 'stock'" class="link add-location" @click="creating = !creating">{{ creating ? '收起新建表单' : '+ 新建库存位置' }}</button>
      <div v-if="action === 'stock' && creating" class="inline-form">
        <label><span>位置名称</span><input v-model.trim="locationForm.name" /></label><label><span>仓库</span><input v-model.trim="locationForm.warehouse" /></label>
        <label><span>货架</span><input v-model.trim="locationForm.shelf" /></label><label><span>位置编码</span><input v-model.trim="locationForm.location_code" /></label>
        <button class="button" :disabled="!locationForm.name || !locationForm.warehouse || !locationForm.location_code" @click="createLocation">创建并选择</button>
      </div>
    </template>
    <label v-else-if="action === 'deploy'"><span>目标机柜</span><select v-model="targetId"><option value="">请选择 Rack</option><option v-for="rack in racks" :key="rack.id" :value="rack.id">{{ rack.name }}{{ rack.model ? ` · ${rack.model}` : '' }}</option></select></label>
    <template v-else-if="action === 'transfer'"><label><span>目标组织</span><select v-model="targetId"><option value="">请选择目标组织</option><option v-for="org in organizations.filter(item => item.is_active)" :key="org.id" :value="org.id">{{ org.name }}</option></select></label><label><span>备注</span><textarea v-model.trim="notes" rows="3" placeholder="请输入调拨备注（选填）"></textarea></label></template>
    <template v-else-if="action === 'retire'"><p class="inline-tip">确认后，关联基础设施对象将标记为退役。</p><label><span>退役原因 *</span><textarea v-model.trim="reason" required rows="3" placeholder="请输入退役原因"></textarea></label><label><span>处置方式</span><select v-model="disposition"><option value="RMA">RMA（返厂维修）</option><option value="SCRAPPED">报废</option><option value="RETURNED_TO_VENDOR">退还供应商</option></select></label></template>
    <template v-else-if="action === 'recover'"><p class="inline-tip">撤销退役后，资产与关联对象将恢复为维护中。</p><label><span>撤销原因 *</span><textarea v-model.trim="reason" required rows="3" placeholder="请输入撤销原因"></textarea></label></template>
    <label v-if="action === 'stock' || action === 'deploy'"><span>操作用户 ID</span><input v-model.trim="operatorId" placeholder="后端要求的用户 UUID" /></label>
    <footer><button class="button" @click="emit('close')">取消</button><button class="button primary" :disabled="submitting || !canSubmit()" @click="submit">{{ submitting ? '提交中…' : '确认' }}</button></footer>
  </section></div>
</template>
