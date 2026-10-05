import { useEffect, useState } from 'react'
import { api } from '../api'
import { CurrentUserContext, STORAGE_KEY } from './currentUser'

export function CurrentUserProvider({ children }) {
  const [userId, setUserId] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved ? Number(saved) : 1
  })
  const [users, setUsers] = useState([])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, String(userId))
  }, [userId])

  useEffect(() => {
    api
      .get('/users')
      .then((res) => setUsers(res.data || []))
      .catch(() => setUsers([]))
  }, [])

  const currentUser = users.find((u) => u.id === userId) || null

  return (
    <CurrentUserContext.Provider value={{ userId, setUserId, users, currentUser }}>
      {children}
    </CurrentUserContext.Provider>
  )
}
