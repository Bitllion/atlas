<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { importApi } from '../api/imports'
import type { ImportPreview } from '../types'

const router = useRouter()
const file = ref<File | null>(null)
const preview = ref<ImportPreview | null>(null)
const uploading = ref(false)
const executing = ref(false)
const completed = ref(false)
const selectedFilename = computed(() => file.value?.name || '')
const canExecute = computed(() => preview.value && preview.value.failed_count === 0 && preview.value.status === 'PREVIEWED')

function selectFile(event: Event) {
  const selected = (event.target as HTMLInputElement).files?.[0] || null
  file.value = selected
  preview.value = null
  completed.value = false
}

async function upload() {
  if (!file.value) return
  uploading.value = true
  try {
    const { data } = await importApi.preview(file.value)
    preview.value = data
  } finally { uploading.value = false }
}

async function execute() {
  if (!preview.value || !canExecute.value) return
  if (!window.confirm(`确认导入 ${preview.value.total_count} 条对象数据吗？`)) return
  executing.value = true
  try {
    const { data } = await importApi.execute(preview.value.import_id)
    preview.value = data
    completed.value = data.status === 'SUCCEEDED'
  } finally { executing.value = false }
}
</script>

<template>
  <section class="page narrow">
    <header class="page-header"><div><p class="eyebrow">DATA INGESTION</p><h1>数据导入</h1><p class="muted">上传设备清单，校验无误后批量创建基础设施对象</p></div><RouterLink class="button" to="/imports">导入历史</RouterLink></header>

    <div class="card upload-card">
      <div><h2>上传文件</h2><p class="muted">支持 .xlsx、.csv，文件首行为模板列名。</p></div>
      <label class="file-picker"><span>{{ selectedFilename || '选择 Excel 或 CSV 文件' }}</span><input type="file" accept=".xlsx,.csv" @change="selectFile" /></label>
      <button class="button primary" :disabled="!file || uploading" @click="upload">{{ uploading ? '正在校验…' : '上传并预览' }}</button>
    </div>
    <div class="template-hint"><strong>模板列</strong><code>name, object_type, serial_number, asset_number, manufacturer, model, status, ownership, management_scope, spec</code><span>其中 name、object_type 必填；spec 填写 JSON 对象字符串。</span></div>

    <template v-if="preview">
      <div class="result-heading"><div><h2>预览结果</h2><span class="status" :class="preview.failed_count ? 'failed' : 'succeeded'">{{ preview.failed_count ? '校验未通过' : '校验通过' }}</span></div><span class="muted">任务 ID：{{ preview.import_id }}</span></div>
      <div class="summary-grid import-summary">
        <div class="summary-card"><strong>{{ preview.total_count }}</strong><span>总行数</span></div>
        <div class="summary-card success"><strong>{{ preview.success_count }}</strong><span>校验成功</span></div>
        <div class="summary-card failure"><strong>{{ preview.failed_count }}</strong><span>校验失败</span></div>
      </div>

      <div v-if="preview.errors.length" class="card table-card error-card">
        <div class="section-title"><h3>错误列表</h3><span class="muted">请修正源文件后重新上传；存在错误时不会写入任何对象。</span></div>
        <div class="table-scroll"><table><thead><tr><th>行号</th><th>字段</th><th>错误类型</th><th>错误信息</th></tr></thead><tbody><tr v-for="(item, index) in preview.errors" :key="`${item.row}-${item.field}-${index}`"><td>{{ item.row }}</td><td>{{ item.field || '—' }}</td><td>{{ item.error_type }}</td><td class="error-message">{{ item.message }}</td></tr></tbody></table></div>
      </div>
      <div v-else class="ready-card card"><span class="ready-icon">✓</span><div><strong>{{ completed ? '导入已完成' : '文件校验通过' }}</strong><p>{{ completed ? `已成功导入 ${preview.success_count} 条对象数据。` : '所有数据均符合要求，可以确认导入。' }}</p></div></div>

      <div class="import-actions">
        <span v-if="preview.failed_count" class="field-error">请修正全部错误并重新上传后再确认导入。</span>
        <RouterLink v-if="completed" class="button primary" to="/objects">查看对象列表</RouterLink>
        <button v-else class="button primary" :disabled="!canExecute || executing" @click="execute">{{ executing ? '正在导入…' : '确认导入' }}</button>
      </div>
    </template>
  </section>
</template>
