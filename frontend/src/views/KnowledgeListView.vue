<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { knowledgeApi, type AskResponse } from '../api/knowledge'
import type { KnowledgeArticle } from '../types'

const router = useRouter()
const items = ref<KnowledgeArticle[]>([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const type = ref('')
const status = ref('')
const pageSize = 20

const question = ref('')
const asking = ref(false)
const askResult = ref<AskResponse | null>(null)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const typeName: Record<string, string> = { SOP: '标准操作流程', TROUBLESHOOTING: '故障排查', FAQ: '常见问题', BEST_PRACTICE: '最佳实践' }
const statusName: Record<string, string> = { DRAFT: '草稿', UNDER_REVIEW: '审核中', PUBLISHED: '已发布', ARCHIVED: '已归档' }

async function load() {
  loading.value = true
  try {
    const { data } = await knowledgeApi.list({ page: page.value, page_size: pageSize, type: type.value || undefined, status: status.value || undefined })
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function filter() {
  page.value = 1
  void load()
}

async function askQuestion() {
  const q = question.value.trim()
  if (!q) return

  asking.value = true
  askResult.value = null
  try {
    const { data } = await knowledgeApi.ask(q)
    askResult.value = data
  } finally {
    asking.value = false
  }
}

function format(v: string) {
  return new Date(v).toLocaleString('zh-CN')
}

onMounted(load)
</script>
<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">KNOWLEDGE CENTER</p>
        <h1>知识库</h1>
        <p class="muted">沉淀基础设施运维经验与标准流程</p>
      </div>
      <RouterLink class="button primary" to="/knowledge/new">+ 新建文章</RouterLink>
    </header>

    <!-- AI 问答区 -->
    <div class="card ai-ask-section">
      <div class="section-title">
        <h3>💬 AI 问答</h3>
      </div>
      <div class="ai-ask-form">
        <form @submit.prevent="askQuestion">
          <label>
            <span>提问</span>
            <textarea v-model="question" rows="3" placeholder="输入您的问题…" :disabled="asking"></textarea>
          </label>
          <button class="button primary" type="submit" :disabled="asking || !question.trim()">
            {{ asking ? '查询中…' : '提问' }}
          </button>
        </form>

        <div v-if="askResult" class="ai-ask-result">
          <div v-if="!askResult.configured" class="ai-not-configured">
            <p>⚠️ LLM 未配置，无法生成 AI 回答。请联系管理员配置 LLM API。</p>
          </div>
          <div v-else-if="askResult.answer" class="ai-answer">
            <strong>AI 回答：</strong>
            <p>{{ askResult.answer }}</p>
          </div>
          <div v-if="askResult.sources.length > 0" class="ai-sources">
            <strong>参考来源：</strong>
            <div v-for="source in askResult.sources" :key="source.id" class="source-item">
              <RouterLink :to="`/knowledge/${source.id}`" class="source-link">
                {{ source.title }} <span class="source-type">({{ typeName[source.type] || source.type }})</span>
              </RouterLink>
              <p class="source-summary">{{ source.summary }}</p>
            </div>
          </div>
          <div v-else-if="!askResult.answer" class="ai-no-result">
            <p>未找到相关知识文章。</p>
          </div>
        </div>
      </div>
    </div>

    <form class="filter-bar card" @submit.prevent="filter">
      <label>
        <span>文章分类</span>
        <select v-model="type">
          <option value="">全部分类</option>
          <option v-for="(name, value) in typeName" :key="value" :value="value">{{ name }}</option>
        </select>
      </label>
      <label>
        <span>发布状态</span>
        <select v-model="status">
          <option value="">全部状态</option>
          <option v-for="(name, value) in statusName" :key="value" :value="value">{{ name }}</option>
        </select>
      </label>
      <button class="button">查询</button>
    </form>

    <div class="card table-card">
      <div v-if="loading" class="empty">正在加载…</div>
      <div v-else-if="!items.length" class="empty">暂无知识文章</div>
      <div v-else class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>标题</th>
              <th>分类</th>
              <th>状态</th>
              <th>标签</th>
              <th>创建时间</th>
              <th>更新时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id" class="clickable" @click="router.push(`/knowledge/${item.id}`)">
              <td class="name-cell">{{ item.title }}</td>
              <td>{{ typeName[item.type] }}</td>
              <td><span class="status" :class="item.status.toLowerCase()">{{ statusName[item.status] }}</span></td>
              <td>{{ item.tags?.join('、') || '—' }}</td>
              <td>{{ format(item.created_at) }}</td>
              <td>{{ format(item.updated_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <footer class="pagination">
        <span>共 {{ total }} 条</span>
        <div>
          <button :disabled="page <= 1" @click="page--; load()">上一页</button>
          <span>第 {{ page }} / {{ totalPages }} 页</span>
          <button :disabled="page >= totalPages" @click="page++; load()">下一页</button>
        </div>
      </footer>
    </div>
  </section>
</template>
