import axios, { AxiosError } from 'axios'
import type { ApiErrorBody } from '../types'

export const apiClient = axios.create({
  baseURL: `${import.meta.env.BASE_URL}api/v1`,
  timeout: 10_000,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('atlas_token')
  if (token) config.headers.Authorization = `Bearer ${token}`

  // 仅用于后端 dev 双通道兼容；正常登录流程不配置该变量。
  const devUserId = import.meta.env.VITE_DEV_USER_ID
  if (devUserId) config.headers['X-User-Id'] = devUserId
  return config
})

export function errorMessage(error: unknown): string {
  if (!axios.isAxiosError<ApiErrorBody>(error)) return '发生未知错误，请稍后重试'
  const body = error.response?.data
  if (body?.message) return body.message
  if (typeof body?.detail === 'string') return body.detail
  if (Array.isArray(body?.detail)) return body.detail.map((item) => item.msg).filter(Boolean).join('；')
  if (error.code === 'ECONNABORTED') return '请求超时，请检查服务状态'
  return error.response ? `请求失败（${error.response.status}）` : '无法连接后端服务'
}

apiClient.interceptors.response.use((response) => response, (error: AxiosError<ApiErrorBody>) => {
  const isLoginRequest = error.config?.url?.endsWith('/auth/login')
  if (error.response?.status === 401 && !isLoginRequest) {
    localStorage.removeItem('atlas_token')
    localStorage.removeItem('atlas_user')
    window.dispatchEvent(new CustomEvent('atlas-auth-unauthorized'))
    if (window.location.pathname !== `${import.meta.env.BASE_URL}login`) {
      window.location.replace(`${import.meta.env.BASE_URL}login`)
    }
    return Promise.reject(error)
  }
  window.dispatchEvent(new CustomEvent('atlas-api-error', { detail: errorMessage(error) }))
  return Promise.reject(error)
})
