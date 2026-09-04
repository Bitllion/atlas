import { apiClient } from './client'
import type { DashboardAssets, DashboardOverview, OperationsSummary, SearchResult } from '../types'

export const dashboardApi = {
  overview: () => apiClient.get<DashboardOverview>('/dashboard/overview'),
  assets: () => apiClient.get<DashboardAssets>('/dashboard/assets'),
  operations: () => apiClient.get<OperationsSummary>('/dashboard/operations'),
  search: (q: string, page = 1, pageSize = 20) => apiClient.get<SearchResult>('/search', { params: { q, page, page_size: pageSize } }),
}
