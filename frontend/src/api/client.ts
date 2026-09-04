import axios, { AxiosError } from 'axios'
import type { ApiErrorBody } from '../types'

export const DEMO_USER_ID = '7c17910d-850b-4a4b-bf93-e556984edab3'
export const apiClient = axios.create({ baseURL: `${import.meta.env.BASE_URL}api/v1`, timeout: 10_000, headers: { 'Content-Type': 'application/json', 'X-User-Id': DEMO_USER_ID } })

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
  window.dispatchEvent(new CustomEvent('atlas-api-error', { detail: errorMessage(error) }))
  return Promise.reject(error)
})
