import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: `${API_BASE}/api`,
})

export function getApiError(err) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join('; ')
  if (detail && typeof detail === 'object') return JSON.stringify(detail)
  return err?.message || 'เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง'
}