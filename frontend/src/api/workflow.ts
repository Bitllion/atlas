import { apiClient } from './client'
import type { Items, WorkflowInstance, WorkflowTask } from '../types'

export const workflowApi = {
  myTasks: () =>
    apiClient.get<Items<WorkflowTask>>('/workflow/tasks/my'),

  approve: (taskId: string, comment?: string) =>
    apiClient.post<WorkflowInstance>(`/workflow/tasks/${taskId}/approve`, { comment: comment || null }),

  reject: (taskId: string, comment?: string) =>
    apiClient.post<WorkflowInstance>(`/workflow/tasks/${taskId}/reject`, { comment: comment || null }),

  getInstance: (instanceId: string) =>
    apiClient.get<WorkflowInstance & { tasks: WorkflowTask[] }>(`/workflow/instances/${instanceId}`),
}
