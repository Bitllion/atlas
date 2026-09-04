import { apiClient } from './client'
import type { Page, QualityDetailItem, QualityOverviewItem, QualityUnattributedItem } from '../types'

export const qualityApi = {
  overview: () =>
    apiClient.get<{ by_type: QualityOverviewItem[] }>('/quality/overview'),

  details: (params: { type?: string; missing?: string; page?: number; page_size?: number }) =>
    apiClient.get<Page<QualityDetailItem>>('/quality/details', { params }),

  unattributed: (page = 1, pageSize = 20) =>
    apiClient.get<Page<QualityUnattributedItem>>('/quality/unattributed', { params: { page, page_size: pageSize } }),
}
