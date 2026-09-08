const API = '/api'

// ระบุตัวตนแบบง่าย (ยังไม่มี login จริง) — เก็บไว้ที่เครื่องผู้ใช้เอง แล้วแนบไปกับทุก
// request เป็น header ให้ backend เช็คสิทธิ์ (ดู backend/utils.py: get_actor)
export function getActor() {
  try {
    const role = localStorage.getItem('actorRole') || 'user'
    const userId = localStorage.getItem('actorUserId') || ''
    const username = localStorage.getItem('actorUsername') || ''
    return { role, userId, username }
  } catch {
    return { role: 'user', userId: '', username: '' }
  }
}

export function setActor({ role, userId, username }) {
  try {
    localStorage.setItem('actorRole', role)
    localStorage.setItem('actorUserId', userId || '')
    localStorage.setItem('actorUsername', username || '')
  } catch { /* localStorage ใช้ไม่ได้ (เช่น private mode) ก็แค่ไม่จำ ไม่ถึงกับพัง */ }
}

function actorHeaders() {
  const { role, userId } = getActor()
  const headers = { 'X-Actor-Role': role }
  if (userId) headers['X-Actor-User-Id'] = String(userId)
  return headers
}

async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...actorHeaders(), ...options.headers },
    ...options,
  })
  if (res.status === 204) return null
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    // FastAPI validation errors (422) ส่ง detail เป็น array ของ object ไม่ใช่ string
    const message = Array.isArray(err.detail)
      ? err.detail.map(d => d.msg).join(', ')
      : err.detail
    throw new Error(message || 'Request failed')
  }
  return res.json()
}

export const favoritesApi = {
  list: () => request(`${API}/favorites/`),
  get: (id) => request(`${API}/favorites/${id}`),
  listByUser: (userId) => request(`${API}/favorites/user/${userId}`),
  create: (data) => request(`${API}/favorites/`, { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`${API}/favorites/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id) => request(`${API}/favorites/${id}`, { method: 'DELETE' }),
}

export const penaltiesApi = {
  list: () => request(`${API}/penalties/`),
  get: (id) => request(`${API}/penalties/${id}`),
  listByUser: (userId) => request(`${API}/penalties/user/${userId}`),
  create: (data) => request(`${API}/penalties/`, { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`${API}/penalties/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id) => request(`${API}/penalties/${id}`, { method: 'DELETE' }),
  applyWeeklyBonus: () => request(`${API}/penalties/weekly-bonus`, { method: 'POST' }),
}

export const usersApi = {
  resolve: (userVal) => request(`${API}/users/resolve/${userVal}`),
}

export const lostItemsApi = {
  list: () => request(`${API}/lost-items/`),
  get: (id) => request(`${API}/lost-items/${id}`),
  create: (data) => request(`${API}/lost-items/`, { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`${API}/lost-items/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id) => request(`${API}/lost-items/${id}`, { method: 'DELETE' }),
}