import { apiClient } from './client'
import type { InfrastructureObject, Items, ObjectDetail, ObjectHistory, ObjectPayload, ObjectType, Page, Relationship, RelationshipType } from '../types'

export interface ObjectFilters { page: number; page_size: number; object_type_id?: string; status?: string; name?: string }
export const objectApi = {
  list: (params: ObjectFilters) => apiClient.get<Page<InfrastructureObject>>('/objects', { params }),
  get: (id: string) => apiClient.get<ObjectDetail>(`/objects/${id}`),
  create: (payload: ObjectPayload) => apiClient.post<InfrastructureObject>('/objects', payload),
  update: (id: string, version: number, payload: ObjectPayload) => apiClient.put<InfrastructureObject>(`/objects/${id}`, payload, { headers: { 'If-Match': String(version) } }),
  remove: (id: string) => apiClient.delete(`/objects/${id}`),
  history: (id: string) => apiClient.get<Items<ObjectHistory>>(`/objects/${id}/history`),
  relations: (params: { source_object_id?: string; target_object_id?: string }) => apiClient.get<Items<Relationship>>('/relationships', { params }),
  types: () => apiClient.get<Items<ObjectType>>('/object-types'),
  relationshipTypes: () => apiClient.get<Items<RelationshipType>>('/relationship-types'),
  racks: () => apiClient.get<Page<InfrastructureObject>>('/objects', { params: { object_type: 'RACK', page: 1, page_size: 200 } }),
}
