import { apiClient } from './client'
import type { Notification, Page } from '../types'

export const notificationsApi = {
  my: (page = 1, pageSize = 20) =>
    apiClient.get<Page<Notification>>('/notifications/my', { params: { page, page_size: pageSize } }),

  unreadCount: () =>
    apiClient.get<{ count: number }>('/notifications/my/unread-count'),

  markRead: (id: string) =>
    apiClient.put<Notification>(`/notifications/${id}/read`),

  markAllRead: () =>
    apiClient.put<{ updated: number }>('/notifications/read-all'),
}
