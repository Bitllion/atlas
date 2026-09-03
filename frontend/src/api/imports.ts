import { apiClient } from './client'
import type { ImportError, ImportJob, ImportPreview, Page } from '../types'

export const importApi = {
  preview: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    form.append('import_type', 'object')
    return apiClient.post<ImportPreview>('/import/preview', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60_000,
    })
  },
  execute: (importId: string) => apiClient.post<ImportPreview>(`/import/${importId}/execute`),
  history: (params: { page: number; page_size: number }) => apiClient.get<Page<ImportJob>>('/import/history', { params }),
  errors: (importId: string, params: { page: number; page_size: number }) => apiClient.get<Page<ImportError>>(`/import/${importId}/errors`, { params }),
}
