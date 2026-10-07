import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: `${API_BASE}/api`,
  withCredentials: true,
})

/** แปลง path ของไฟล์จาก backend (เช่น /api/uploads/x.jpg) เป็น URL เต็ม
 * รองรับกรณีตั้ง VITE_API_URL เป็นคนละ origin กับหน้าเว็บ */
export function assetUrl(path) {
  if (!path) return path
  if (/^https?:/i.test(path)) return path
  return `${API_BASE}${path}`
}

export const authLoginUrl = `${API_BASE}/api/auth/google/login`

export function getApiError(err) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join('; ')
  if (detail && typeof detail === 'object') return JSON.stringify(detail)
  return err?.message || 'เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง'
}