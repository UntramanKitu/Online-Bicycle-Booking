import { useEffect, useState } from 'react'
import { api } from '../api'
import { CurrentUserContext } from './currentUser'

export function CurrentUserProvider({ children }) {
  // ผู้ใช้ตัวจริงจาก Google OAuth session (cookie bikea_access_token)
  // ไม่มี mock / ไม่มีสลับ user แล้ว
  const [currentUser, setCurrentUser] = useState(null)
  const [usersLoading, setUsersLoading] = useState(true)
  // รายชื่อผู้ใช้ทุกคน (/api/users) — ใช้แมป user_id → ชื่อจริงในมุมมอง "ทั้งระบบ" ของแอดมิน
  const [allUsers, setAllUsers] = useState([])
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    api
      .get('/auth/me')
      .then((res) => {
        if (res.data?.authenticated && res.data?.user) {
          setCurrentUser(res.data.user)
        } else {
          setCurrentUser(null)
        }
      })
      .catch(() => setCurrentUser(null))
      .finally(() => setUsersLoading(false))
  }, [])

  const userId = currentUser?.id ?? null
  // แอดมิน = role จาก backend (is_staff / AUTH_ADMIN_EMAILS) — เห็นข้อมูลของทุกคนในระบบ
  const isAdmin = currentUser?.role === 'admin'
  const users = allUsers.length > 0 ? allUsers : currentUser ? [currentUser] : []

  // โหลดรายชื่อผู้ใช้ครั้งเดียวหลังล็อกอิน — ใช้แปลง user_id เป็นชื่อจริงทั่วทั้งแอป
  useEffect(() => {
    if (!currentUser) {
      // เลื่อนไป task ถัดไป — กันกฎ react-hooks/set-state-in-effect (sync setState ใน effect)
      const timer = window.setTimeout(() => setAllUsers([]), 0)
      return () => window.clearTimeout(timer)
    }
    let alive = true
    api
      .get('/users')
      .then((res) => { if (alive) setAllUsers(res.data || []) })
      .catch(() => { /* แมปชื่อไม่ได้ไม่เป็นไร — fallback เป็น "ผู้ใช้ #id" */ })
    return () => { alive = false }
  }, [currentUser])

  // โหลดแจ้งเตือนของคนล็อกอิน — ใช้โชว์ badge ที่กระดิ่ง header
  const refreshNotifications = async () => {
    if (!currentUser?.id) {
      setNotifications([])
      setUnreadCount(0)
      return []
    }
    try {
      const res = await api.get(`/notifications/user/${currentUser.id}`)
      const list = res.data || []
      setNotifications(list)
      setUnreadCount(list.filter((n) => !n.is_read).length)
      return list
    } catch {
      return []
    }
  }

  useEffect(() => {
    if (!currentUser?.id) return
    // เลื่อนไป task ถัดไป — กันกฎ react-hooks/set-state-in-effect (sync setState ใน effect)
    const timer = window.setTimeout(() => refreshNotifications(), 0)
    const interval = window.setInterval(() => refreshNotifications(), 60000)
    return () => { window.clearTimeout(timer); window.clearInterval(interval) }
  }, [currentUser?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  const markNotificationRead = async (id) => {
    try {
      await api.patch(`/notifications/${id}/read`)
      setNotifications((list) => list.map((n) => (n.id === id ? { ...n, is_read: true } : n)))
      setUnreadCount((c) => Math.max(0, c - 1))
    } catch {
      // เงียบไว้ — badge จะซิงก์ใหม่รอบหน้า
    }
  }

  // ล้างข้อความที่อ่านแล้วทั้งหมดในทีเดียว — คืนจำนวนที่ลบ
  const clearReadNotifications = async () => {
    if (!currentUser?.id) return 0
    try {
      const res = await api.delete(`/notifications/user/${currentUser.id}/read`)
      const deleted = res.data?.deleted ?? 0
      setNotifications((list) => list.filter((n) => !n.is_read))
      return deleted
    } catch {
      return 0
    }
  }

  // โหลดข้อมูลตัวเองใหม่จาก /auth/me — ใช้ตอนแก้โปรไฟล์ให้ชื่อใหม่แทนที่ทันที
  const refreshUser = async () => {
    try {
      const res = await api.get('/auth/me')
      setCurrentUser(res.data?.authenticated && res.data?.user ? res.data.user : null)
      return res.data?.user ?? null
    } catch {
      setCurrentUser(null)
      return null
    }
  }

  // แปลง user_id เป็นชื่อจริงจาก /api/users — ไม่พบค่อย fallback เป็น "ผู้ใช้ #id"
  const getUserName = (id) => {
    if (id == null) return '-'
    const found = allUsers.find((u) => Number(u.id) === Number(id))
    if (found) return found.full_name || found.username
    if (currentUser && Number(id) === currentUser.id) return currentUser.full_name || currentUser.username
    return `ผู้ใช้ #${id}`
  }

  return (
    <CurrentUserContext.Provider
      value={{ userId, users, usersLoading, currentUser, isAdmin, getUserName, notifications, unreadCount, refreshNotifications, markNotificationRead, clearReadNotifications, refreshUser }}
    >
      {children}
    </CurrentUserContext.Provider>
  )
}
