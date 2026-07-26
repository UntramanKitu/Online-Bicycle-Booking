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

export const returnsApi = {
  list: () => request(`${API}/returns/`),
  get: (id) => request(`${API}/returns/${id}`),
  create: (data) => request(`${API}/returns/`, { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`${API}/returns/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id) => request(`${API}/returns/${id}`, { method: 'DELETE' }),
}

export const damagesApi = {
  list: () => request(`${API}/damages/`),
  get: (id) => request(`${API}/damages/${id}`),
  create: (formData) => fetch(`${API}/damages/`, { method: 'POST', body: formData }).then(r => r.json()),
  update: (id, formData) => fetch(`${API}/damages/${id}`, { method: 'PUT', body: formData }).then(r => r.json()),
  delete: (id) => request(`${API}/damages/${id}`, { method: 'DELETE' }),
}

export const favoritesApi = {
  list: () => request(`${API}/favorites/`),
  get: (id) => request(`${API}/favorites/${id}`),
  listByUser: (userId) => request(`${API}/favorites/user/${userId}`),
  create: (data) => request(`${API}/favorites/`, { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`${API}/favorites/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id) => request(`${API}/favorites/${id}`, { method: 'DELETE' }),
}
