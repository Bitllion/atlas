import { apiClient } from './client'
import type { Organization, OrganizationType, Page, User } from '../types'

export const adminApi = {
  users: (params: { search?: string; page: number; page_size: number }) => apiClient.get<Page<User>>('/users', { params }),
  createUser: (payload: { username: string; full_name?: string | null; email: string; organization_id: string }) => apiClient.post<User>('/users', payload),
  updateUser: (id: string, payload: { full_name?: string | null; email?: string; organization_id?: string; is_active?: boolean }) => apiClient.put<User>(`/users/${id}`, payload),
  organizations: (params: { search?: string; page: number; page_size: number }) => apiClient.get<Page<Organization>>('/organizations', { params }),
  createOrganization: (payload: { name: string; org_type: OrganizationType }) => apiClient.post<Organization>('/organizations', payload),
  updateOrganization: (id: string, payload: { name?: string; is_active?: boolean }) => apiClient.put<Organization>(`/organizations/${id}`, payload),
}
