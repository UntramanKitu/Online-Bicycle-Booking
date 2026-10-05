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

  // แปลง user_id เป็นชื่อจริง สำหรับจุดที่เคยแสดงแค่ "#1" ให้อ่านรู้เรื่องกัน
  const getUserName = (id) => {
    if (id == null) return '-'
    const found = users.find((u) => u.id === Number(id))
    return found ? found.full_name : `ผู้ใช้ #${id}`
  }

  return (
    <CurrentUserContext.Provider
      value={{ userId, setUserId, users, currentUser, getUserName }}
    >
      {children}
    </CurrentUserContext.Provider>
  )
}
