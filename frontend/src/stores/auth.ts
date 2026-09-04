import { ref } from 'vue'
import { apiClient } from '../api/client'

export interface AuthUser {
  id: string
  username: string
  full_name: string | null
  organization_id: string | null
  roles: string[]
}

interface LoginResponse {
  access_token: string
  user: AuthUser
}

function storedUser(): AuthUser | null {
  try {
    return JSON.parse(localStorage.getItem('atlas_user') || 'null') as AuthUser | null
  } catch {
    localStorage.removeItem('atlas_user')
    return null
  }
}

export const currentUser = ref<AuthUser | null>(storedUser())

export async function login(username: string, password: string): Promise<void> {
  const { data } = await apiClient.post<LoginResponse>('/auth/login', { username, password })
  localStorage.setItem('atlas_token', data.access_token)
  localStorage.setItem('atlas_user', JSON.stringify(data.user))
  currentUser.value = data.user
}

export function logout(): void {
  localStorage.removeItem('atlas_token')
  localStorage.removeItem('atlas_user')
  currentUser.value = null
}
