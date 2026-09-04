import { apiClient } from './client'
import type { ArticleLink, ArticlePayload, InfrastructureObject, Items, KnowledgeArticle, KnowledgeArticleDetail, Page } from '../types'

export const knowledgeApi = {
  list: (params: { page: number; page_size: number; type?: string; status?: string }) => apiClient.get<Page<KnowledgeArticle>>('/knowledge/articles', { params }),
  get: (id: string) => apiClient.get<KnowledgeArticleDetail>(`/knowledge/articles/${id}`),
  create: (payload: ArticlePayload) => apiClient.post<KnowledgeArticle>('/knowledge/articles', payload),
  publish: (id: string) => apiClient.post<KnowledgeArticle>(`/knowledge/articles/${id}/publish`),
  upload: (id: string, file: File) => { const data = new FormData(); data.append('file', file); return apiClient.post(`/knowledge/articles/${id}/attachments`, data, { headers: { 'Content-Type': 'multipart/form-data' } }) },
  linkObjects: (id: string, objects: string[], relationReason?: string) => apiClient.post<Items<ArticleLink>>(`/knowledge/articles/${id}/link-objects`, { objects, relation_reason: relationReason || null }),
  objects: () => apiClient.get<Page<InfrastructureObject>>('/objects', { params: { page: 1, page_size: 100 } }),
  downloadAttachment: (articleId: string, attachmentId: string) => apiClient.get<Blob>(`/knowledge/articles/${articleId}/attachments/${attachmentId}/download`, { responseType: 'blob' }),
}
