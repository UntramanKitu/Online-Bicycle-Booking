const API = '/api'

async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (res.status === 204) return null
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
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
}

export const lostItemsApi = {
  list: () => request(`${API}/lost-items/`),
  get: (id) => request(`${API}/lost-items/${id}`),
  create: (data) => request(`${API}/lost-items/`, { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`${API}/lost-items/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id) => request(`${API}/lost-items/${id}`, { method: 'DELETE' }),
}

export const pointsApi = {
  list: () => request(`${API}/points/`),
  listByUser: (userId) => request(`${API}/points/user/${userId}`),
  add: (data) => request(`${API}/points/add`, { method: 'POST', body: JSON.stringify(data) }),
}