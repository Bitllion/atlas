<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { IconRefresh } from '@arco-design/web-vue/es/icon'
import { Message } from '@arco-design/web-vue'
import { workflowApi } from '../api/workflow'
import type { WorkflowTask } from '../types'
const tasks = ref<WorkflowTask[]>([]), loading = ref(false), actioningTaskId = ref<string | null>(null), showCommentModal = ref(false)
const currentAction = ref<'approve' | 'reject'>('approve'), currentTaskId = ref(''), comment = ref('')
async function loadTasks() { loading.value = true; try { tasks.value = (await workflowApi.myTasks()).data.items.filter(task => task.status === 'PENDING') } finally { loading.value = false } }
function openCommentModal(taskId: string, action: 'approve' | 'reject') { currentTaskId.value = taskId; currentAction.value = action; comment.value = ''; showCommentModal.value = true }
async function executeAction() { if (!currentTaskId.value) return; actioningTaskId.value = currentTaskId.value; try { if (currentAction.value === 'approve') await workflowApi.approve(currentTaskId.value, comment.value || undefined); else await workflowApi.reject(currentTaskId.value, comment.value || undefined); showCommentModal.value = false; await loadTasks(); Message.success(currentAction.value === 'approve' ? '审批已批准' : '审批已驳回') } finally { actioningTaskId.value = null } }
function cancelModal() { showCommentModal.value = false; currentTaskId.value = ''; comment.value = '' }
onMounted(() => { void loadTasks() })
</script>
<template><section class="page arco-page"><header class="page-header"><div><p class="eyebrow">工作流</p><h1>我的审批</h1><p class="muted">处理分配给我的待办审批任务</p></div><a-button @click="loadTasks"><template #icon><IconRefresh /></template>刷新</a-button></header>
<a-card class="arco-table-card" :bordered="false"><a-table :data="tasks" :loading="loading" :pagination="false" row-key="id" :scroll="{ x: 1000 }"><template #columns><a-table-column title="任务 ID" data-index="id" :width="240" ellipsis tooltip /><a-table-column title="流程实例 ID" data-index="instance_id" :width="240" ellipsis tooltip /><a-table-column title="审批节点" data-index="node_id" :width="180" /><a-table-column title="创建时间" :width="180"><template #cell="{ record }">{{ new Date(record.created_at).toLocaleString('zh-CN') }}</template></a-table-column><a-table-column title="操作" fixed="right" :width="150"><template #cell="{ record }"><a-space><a-button type="text" size="small" :disabled="actioningTaskId === record.id" @click="openCommentModal(record.id, 'approve')">批准</a-button><a-button type="text" status="danger" size="small" :disabled="actioningTaskId === record.id" @click="openCommentModal(record.id, 'reject')">驳回</a-button></a-space></template></a-table-column></template><template #empty><a-empty description="暂无待审批任务" /></template></a-table><div class="arco-pagination"><span>共 {{ tasks.length }} 条待办</span></div></a-card>
<a-modal v-model:visible="showCommentModal" :title="currentAction === 'approve' ? '批准审批' : '驳回审批'" :ok-text="currentAction === 'approve' ? '确认批准' : '确认驳回'" cancel-text="取消" :ok-loading="actioningTaskId !== null" :ok-button-props="{ status: currentAction === 'reject' ? 'danger' : 'normal' }" @ok="executeAction" @cancel="cancelModal"><a-alert :type="currentAction === 'approve' ? 'info' : 'warning'">请确认审批决定，操作完成后将进入下一流程节点。</a-alert><a-form :model="{}" layout="vertical" class="modal-note-form"><a-form-item label="审批意见"><a-textarea v-model="comment" :auto-size="{ minRows: 4, maxRows: 7 }" placeholder="请输入审批意见（可选）" /></a-form-item></a-form></a-modal>
</section></template>
