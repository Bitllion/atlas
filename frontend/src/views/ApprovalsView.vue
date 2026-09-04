<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { workflowApi } from '../api/workflow'
import type { WorkflowTask } from '../types'

const tasks = ref<WorkflowTask[]>([])
const loading = ref(false)
const actioningTaskId = ref<string | null>(null)
const showCommentModal = ref(false)
const currentAction = ref<'approve' | 'reject'>('approve')
const currentTaskId = ref<string>('')
const comment = ref('')

async function loadTasks() {
  loading.value = true
  try {
    const { data } = await workflowApi.myTasks()
    tasks.value = data.items.filter(task => task.status === 'PENDING')
  } finally {
    loading.value = false
  }
}

function openCommentModal(taskId: string, action: 'approve' | 'reject') {
  currentTaskId.value = taskId
  currentAction.value = action
  comment.value = ''
  showCommentModal.value = true
}

async function executeAction() {
  if (!currentTaskId.value) return

  actioningTaskId.value = currentTaskId.value
  try {
    if (currentAction.value === 'approve') {
      await workflowApi.approve(currentTaskId.value, comment.value || undefined)
    } else {
      await workflowApi.reject(currentTaskId.value, comment.value || undefined)
    }
    showCommentModal.value = false
    await loadTasks()
  } finally {
    actioningTaskId.value = null
  }
}

function cancelModal() {
  showCommentModal.value = false
  currentTaskId.value = ''
  comment.value = ''
}

onMounted(() => {
  void loadTasks()
})
</script>

<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">WORKFLOW</p>
        <h1>我的审批</h1>
        <p class="muted">待处理的审批任务</p>
      </div>
      <button class="button" @click="loadTasks">刷新</button>
    </header>

    <div class="card table-card">
      <div v-if="loading" class="empty">正在加载…</div>
      <div v-else-if="tasks.length === 0" class="empty">暂无待审批任务</div>
      <div v-else class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>任务 ID</th>
              <th>流程实例 ID</th>
              <th>节点 ID</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="task in tasks" :key="task.id">
              <td class="id-cell">{{ task.id }}</td>
              <td class="id-cell">{{ task.instance_id }}</td>
              <td>{{ task.node_id }}</td>
              <td>{{ new Date(task.created_at).toLocaleString('zh-CN') }}</td>
              <td class="actions">
                <button
                  class="link"
                  :disabled="actioningTaskId === task.id"
                  @click="openCommentModal(task.id, 'approve')"
                >
                  批准
                </button>
                <button
                  class="link danger"
                  :disabled="actioningTaskId === task.id"
                  @click="openCommentModal(task.id, 'reject')"
                >
                  驳回
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="showCommentModal" class="modal-mask" @click.self="cancelModal">
      <div class="modal card">
        <header>
          <h2>{{ currentAction === 'approve' ? '批准审批' : '驳回审批' }}</h2>
          <button class="modal-close" type="button" @click="cancelModal">×</button>
        </header>
        <label>
          <span>备注（可选）</span>
          <textarea v-model="comment" rows="4" placeholder="输入审批意见…"></textarea>
        </label>
        <footer>
          <button class="button" type="button" @click="cancelModal">取消</button>
          <button
            class="button primary"
            type="button"
            :disabled="actioningTaskId !== null"
            @click="executeAction"
          >
            {{ actioningTaskId ? '处理中…' : '确认' }}
          </button>
        </footer>
      </div>
    </div>
  </section>
</template>
