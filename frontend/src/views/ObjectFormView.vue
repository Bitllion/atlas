<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { objectApi } from '../api/objects'
import type { ManagementScope, ObjectPayload, ObjectStatus, ObjectType, Ownership } from '../types'

const route = useRoute(); const router = useRouter(); const id = computed(() => route.params.id as string | undefined)
const types = ref<ObjectType[]>([]); const saving = ref(false); const version = ref(1); const specText = ref('{}'); const validationError = ref('')
const form = reactive({ object_type_id: '', name: '', serial_number: '', asset_number: '', manufacturer: '', model: '', firmware_version: '', hardware_generation: '', status: 'PLANNED' as ObjectStatus, ownership: 'OWNED' as Ownership, management_scope: 'NO_ACCESS' as ManagementScope, owner_org_id: '', operator_org_id: '', maintainer_org_id: '', deployed_location_id: '' })
const title = computed(() => id.value ? '编辑对象' : '新建对象')
function nullable(value: string) { return value.trim() || null }
async function submit() {
  validationError.value = ''
  let spec_data: Record<string, unknown>
  try { const parsed: unknown = JSON.parse(specText.value || '{}'); if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error(); spec_data = parsed as Record<string, unknown> } catch { validationError.value = 'Specification 必须是有效的 JSON 对象'; return }
  const payload: ObjectPayload = { ...form, serial_number: nullable(form.serial_number), asset_number: nullable(form.asset_number), manufacturer: nullable(form.manufacturer), model: nullable(form.model), firmware_version: nullable(form.firmware_version), hardware_generation: nullable(form.hardware_generation), owner_org_id: nullable(form.owner_org_id), operator_org_id: nullable(form.operator_org_id), maintainer_org_id: nullable(form.maintainer_org_id), deployed_location_id: nullable(form.deployed_location_id), spec_data }
  saving.value = true
  try { const response = id.value ? await objectApi.update(id.value, version.value, payload) : await objectApi.create(payload); await router.push(`/objects/${response.data.id}`) } finally { saving.value = false }
}
onMounted(async () => {
  types.value = (await objectApi.types()).data.items
  if (!id.value) return
  const { data } = await objectApi.get(id.value); version.value = data.version
  Object.assign(form, Object.fromEntries(Object.keys(form).map((key) => [key, (data as unknown as Record<string, unknown>)[key] ?? ''])))
  specText.value = JSON.stringify(data.spec_data, null, 2)
})
</script>

<template><section class="page narrow"><header class="page-header"><div><RouterLink class="back" :to="id ? `/objects/${id}` : '/objects'">← 返回</RouterLink><h1>{{ title }}</h1><p class="muted">维护对象基础属性、管理边界与技术规格</p></div></header>
  <form class="card object-form" @submit.prevent="submit"><h2>基础信息</h2><div class="form-grid">
    <label><span>对象类型 *</span><select v-model="form.object_type_id" required :disabled="!!id"><option value="" disabled>请选择</option><option v-for="item in types" :key="item.id" :value="item.id">{{ item.display_name || item.name }}</option></select></label>
    <label><span>名称 *</span><input v-model.trim="form.name" required maxlength="255" /></label><label><span>序列号</span><input v-model.trim="form.serial_number" /></label><label><span>资产编号</span><input v-model.trim="form.asset_number" /></label><label><span>制造商</span><input v-model.trim="form.manufacturer" /></label><label><span>型号</span><input v-model.trim="form.model" /></label><label><span>固件版本</span><input v-model.trim="form.firmware_version" /></label><label><span>硬件代际</span><input v-model.trim="form.hardware_generation" /></label>
    <label><span>状态</span><select v-model="form.status"><option value="PLANNED">计划中</option><option value="ACTIVE">运行中</option><option value="INACTIVE">未启用</option><option value="MAINTENANCE">维护中</option><option value="RETIRED">已退役</option></select></label>
    <label><span>所有权</span><select v-model="form.ownership"><option value="OWNED">自有</option><option value="CUSTOMER_OWNED">客户所有</option><option value="THIRD_PARTY">第三方</option></select></label>
    <label><span>管理范围</span><select v-model="form.management_scope"><option value="FULL_CONTROL">完全控制</option><option value="HARDWARE_ONLY">仅硬件</option><option value="MAINTENANCE_ONLY">仅维保</option><option value="NO_ACCESS">无访问权</option></select></label>
    <label><span>所有者组织 ID</span><input v-model.trim="form.owner_org_id" placeholder="UUID（可选）" /></label><label><span>运营组织 ID</span><input v-model.trim="form.operator_org_id" placeholder="UUID（可选）" /></label><label><span>维保组织 ID</span><input v-model.trim="form.maintainer_org_id" placeholder="UUID（可选）" /></label><label><span>部署位置对象 ID</span><input v-model.trim="form.deployed_location_id" placeholder="UUID（可选）" /></label>
  </div><h2>Specification</h2><label><span>JSON 规格数据</span><textarea v-model="specText" rows="12" spellcheck="false"></textarea></label><p v-if="validationError" class="field-error">{{ validationError }}</p>
  <footer class="form-actions"><RouterLink class="button" :to="id ? `/objects/${id}` : '/objects'">取消</RouterLink><button class="button primary" :disabled="saving" type="submit">{{ saving ? '保存中…' : '保存对象' }}</button></footer></form>
</section></template>
