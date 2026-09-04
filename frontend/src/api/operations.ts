import { apiClient } from './client'
import type { Page, RepairRecord, ReplacementEvent, WorkOrder, WorkOrderDetail, WorkOrderPriority, WorkOrderTimelineEvent, WorkOrderType } from '../types'

export interface WorkOrderCreatePayload { title: string; type: WorkOrderType; priority: WorkOrderPriority; object_id: string; description?: string | null }
export interface RepairPayload { object_id?: string; repair_type: string; description: string; repair_result: string; engineer_id?: string; started_at?: string; completed_at?: string; verification_notes?: string | null }
export interface ReplacementPayload { repair_record_id?: string; old_object_id: string; new_object_id: string; replacement_reason: string; old_object_disposition: string; engineer_id?: string; replaced_at?: string; notes?: string | null }

export const operationsApi = {
  list: (params: { status?: string; type?: string; page: number; page_size: number }) => apiClient.get<Page<WorkOrder>>('/work-orders', { params }),
  get: (id: string) => apiClient.get<WorkOrderDetail>(`/work-orders/${id}`),
  timeline: (id: string) => apiClient.get<{ work_order_id: string; items: WorkOrderTimelineEvent[] }>(`/work-orders/${id}/timeline`),
  create: (payload: WorkOrderCreatePayload) => apiClient.post<WorkOrder>('/work-orders', payload),
  assign: (id: string, assigned_to: string) => apiClient.put<WorkOrder>(`/work-orders/${id}/assign`, { assigned_to }),
  start: (id: string) => apiClient.put<WorkOrder>(`/work-orders/${id}/start`),
  resolve: (id: string) => apiClient.put<WorkOrder>(`/work-orders/${id}/resolve`),
  close: (id: string) => apiClient.put<WorkOrder>(`/work-orders/${id}/close`),
  repair: (id: string, payload: RepairPayload) => apiClient.post<RepairRecord>(`/work-orders/${id}/repairs`, payload),
  replacement: (id: string, payload: ReplacementPayload) => apiClient.post<ReplacementEvent>(`/work-orders/${id}/replacements`, payload),
}
