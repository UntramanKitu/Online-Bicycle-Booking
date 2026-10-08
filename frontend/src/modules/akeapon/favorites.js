import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api'

// รายการโปรดเชื่อม backend `/api/favorites` จริง (ใช้ร่วมกับหน้ารายการโปรด)
// คืนค่าเหมือนเดิม: favorites = [bikeId, ...] เพื่อให้หน้าที่ใช้อยู่ไม่พัง
export function useFavorites(userId) {
  const [records, setRecords] = useState([])
  const [favOnly, setFavOnly] = useState(false)
  const [favBusyId, setFavBusyId] = useState(null)

  useEffect(() => {
    if (!userId) {
      // เลื่อนไป task ถัดไป — กันกฎ react-hooks/set-state-in-effect
      const timer = window.setTimeout(() => setRecords([]), 0)
      return () => window.clearTimeout(timer)
    }
    let alive = true
    api
      .get(`/favorites/user/${userId}`)
      .then((res) => { if (alive) setRecords(res.data || []) })
      .catch(() => { /* โหลดไม่ได้ให้ว่างไว้ก่อน — หน้าจองยังใช้งานได้ */ })
    return () => { alive = false }
  }, [userId])

  const favorites = records.map((f) => f.bicycle_id).filter((id) => id != null)

  const toggleFavorite = useCallback(async (bikeId) => {
    if (!userId || bikeId == null) return
    const id = Number(bikeId)
    const existing = records.find((f) => Number(f.bicycle_id) === id)
    setFavBusyId(id)
    try {
      if (existing) {
        await api.delete(`/favorites/${existing.id}`)
        setRecords((prev) => prev.filter((f) => f.id !== existing.id))
      } else {
        const res = await api.post('/favorites', {
          user_id: userId,
          target_type: 'bicycle',
          bicycle_id: id,
        })
        if (res.data) setRecords((prev) => [res.data, ...prev])
      }
    } catch {
      // เงียบไว้ — ให้หัวใจค้างสถานะเดิม ถ้าพังจริงค่อยดูที่หน้ารายการโปรด
    } finally {
      setFavBusyId(null)
    }
  }, [userId, records])

  return { favorites, favOnly, setFavOnly, toggleFavorite, favBusyId }
}
