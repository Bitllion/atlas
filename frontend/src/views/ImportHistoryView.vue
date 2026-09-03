<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { importApi } from '../api/imports'
import type { ImportError, ImportJob } from '../types'

const jobs = ref<ImportJob[]>([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const selectedId = ref('')
const errors = ref<ImportError[]>([])
const errorsTotal = ref(0)
const loadingErrors = ref(false)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const statusText: Record<string, string> = { PREVIEWED: '已预览', EXECUTING: '执行中', SUCCEEDED: '成功', FAILED: '失败' }
function formatTime(value: string) { return new Date(value).toLocaleString('zh-CN') }

async function load() {
  loading.value = true
  selectedId.value = ''; errors.value = []
  try {
    const { data } = await importApi.history({ page: page.value, page_size: pageSize })
    jobs.value = data.items; total.value = data.total
  } finally { loading.value = false }
}
function changePage(value: number) { page.value = value; void load() }
async function toggleErrors(job: ImportJob) {
  if (selectedId.value === job.id) { selectedId.value = ''; errors.value = []; return }
  selectedId.value = job.id; loadingErrors.value = true
  try {
    const { data } = await importApi.errors(job.id, { page: 1, page_size: 200 })
    errors.value = data.items; errorsTotal.value = data.total
  } finally { loadingErrors.value = false }
}
onMounted(load)
</script>

<template>
  <section class="page">
    <header class="page-header"><div><RouterLink class="back" to="/import">← 返回数据导入</RouterLink><p class="eyebrow">DATA INGESTION</p><h1>导入历史</h1><p class="muted">查看导入任务状态和校验错误</p></div><RouterLink class="button primary" to="/import">新建导入</RouterLink></header>
    <div class="card table-card">
      <div v-if="loading" class="empty">正在加载…</div>
      <div v-else-if="!jobs.length" class="empty">暂无导入记录</div>
      <div v-else class="table-scroll"><table><thead><tr><th>文件名</th><th>格式</th><th>创建时间</th><th>状态</th><th>总数</th><th>成功</th><th>失败</th><th>操作</th></tr></thead><tbody>
        <template v-for="job in jobs" :key="job.id">
          <tr><td class="name-cell">{{ job.filename }}</td><td>{{ job.format }}</td><td>{{ formatTime(job.created_at) }}</td><td><span class="status" :class="job.status.toLowerCase()">{{ statusText[job.status] || job.status }}</span></td><td>{{ job.total_rows }}</td><td>{{ job.success_count }}</td><td>{{ job.failed_count }}</td><td><button class="link" @click="toggleErrors(job)">{{ selectedId === job.id ? '收起详情' : '查看错误' }}</button></td></tr>
          <tr v-if="selectedId === job.id" class="expanded-row"><td colspan="8"><div v-if="loadingErrors" class="inline-empty">正在加载错误详情…</div><div v-else-if="!errors.length" class="inline-empty">该任务没有错误记录</div><div v-else class="nested-errors"><div class="section-title"><strong>错误详情</strong><span class="muted">共 {{ errorsTotal }} 条</span></div><table><thead><tr><th>行号</th><th>字段</th><th>错误类型</th><th>错误信息</th></tr></thead><tbody><tr v-for="(item, index) in errors" :key="`${item.row}-${index}`"><td>{{ item.row }}</td><td>{{ item.field || '—' }}</td><td>{{ item.error_type }}</td><td class="error-message">{{ item.message }}</td></tr></tbody></table></div></td></tr>
        </template>
      </tbody></table></div>
      <footer class="pagination"><span>共 {{ total }} 条</span><div><button :disabled="page <= 1" @click="changePage(page - 1)">上一页</button><span>第 {{ page }} / {{ totalPages }} 页</span><button :disabled="page >= totalPages" @click="changePage(page + 1)">下一页</button></div></footer>
    </div>
  </section>
</template>
