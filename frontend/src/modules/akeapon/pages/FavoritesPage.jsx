import { useEffect, useMemo, useState } from 'react'
import { api, getApiError } from '../../../api'
import { formatDateTime } from '../../../utils'
import { useCurrentUser } from '../../../context/currentUser'
import '../akeapon.css'

// รายการโปรดของผู้ใช้ — เชื่อม backend `/api/favorites` จริง (ไม่ใช่ localStorage แล้ว)
export default function FavoritesPage() {
  const { userId, usersLoading } = useCurrentUser()
  const [favorites, setFavorites] = useState([])
  const [bikes, setBikes] = useState([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [editName, setEditName] = useState('')
  const [editSaving, setEditSaving] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const [favRes, bikeRes] = await Promise.all([
        api.get(`/favorites/user/${userId}`),
        api.get('/bicycles'),
      ])
      setFavorites(favRes.data || [])
      setBikes(bikeRes.data || [])
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (usersLoading || !userId) return
    // เลื่อนไป task ถัดไป — กันกฎ react-hooks/set-state-in-effect
    const timer = window.setTimeout(() => load(), 0)
    return () => window.clearTimeout(timer)
  }, [userId, usersLoading]) // eslint-disable-line react-hooks/exhaustive-deps

  const bikeById = useMemo(() => new Map(bikes.map((b) => [b.id, b])), [bikes])

  async function handleRemove(id) {
    setMessage(null)
    try {
      await api.delete(`/favorites/${id}`)
      setFavorites((prev) => prev.filter((f) => f.id !== id))
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    }
  }

  function startEdit(fav) {
    setMessage(null)
    setEditingId(fav.id)
    setEditName(fav.nickname || '')
  }

  function cancelEdit() {
    setEditingId(null)
    setEditName('')
  }

  async function handleRename(e) {
    e.preventDefault()
    if (!editingId) return
    const name = editName.trim()
    setEditSaving(true)
    setMessage(null)
    try {
      const res = await api.put(`/favorites/${editingId}`, { nickname: name || null })
      setFavorites((prev) => prev.map((f) => (f.id === editingId ? res.data : f)))
      setMessage({ type: 'success', text: name ? 'แก้ชื่อแล้ว ✓' : 'ล้างชื่อแล้ว ✓' })
      cancelEdit()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setEditSaving(false)
    }
  }

  if (!usersLoading && !userId) {
    return <p className="empty">กรุณาเข้าสู่ระบบก่อนใช้งาน</p>
  }

  return (
    <div className="page-section">
      <div className="section-head">
        <div>
          <h1 className="section-title">รายการโปรด</h1>
          <p className="section-subtitle">จักรยานที่คุณกดไว้ ♥ เรียกดูได้ทันที</p>
        </div>
      </div>

      {message && (
        <div className={`alert ${message.type === 'error' ? 'alert-error' : 'alert-success'}`}>
          {message.text}
        </div>
      )}

      {loading ? (
        <p className="empty">กำลังโหลดรายการโปรด...</p>
      ) : favorites.length === 0 ? (
        <p className="empty">ยังไม่มีจักรยานในรายการโปรด — กด ♡ ที่หน้าจองจักรยานเพื่อเพิ่มได้เลย</p>
      ) : (
        <div className="score-grid">
          {favorites.map((fav) => {
            const bike = bikeById.get(fav.bicycle_id)
            return (
              <section key={fav.id} className="ticket-card">
                <header>
                  {fav.nickname || bike?.model || `จักรยาน #${fav.bicycle_id}`}
                </header>
                {editingId === fav.id ? (
                  <form className="fav-rename-form" onSubmit={handleRename}>
                    <input
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      placeholder="ตั้งชื่อเรียก เช่น คันประจำ"
                      maxLength={100}
                      aria-label="ชื่อเรียกรายการโปรด"
                    />
                    <div className="fav-rename-actions">
                      <button className="btn btn-sm btn-primary" type="submit" disabled={editSaving}>
                        {editSaving ? 'กำลังบันทึก...' : 'บันทึก'}
                      </button>
                      <button className="btn btn-sm btn-ghost" type="button" onClick={cancelEdit} disabled={editSaving}>
                        ยกเลิก
                      </button>
                    </div>
                  </form>
                ) : null}
                <ul className="score-events">
                  <li>
                    <span className="score-delta plus">♥</span>
                    <span className="score-reason">
                      <strong>{bike ? `${bike.code} · ${bike.model}` : `จักรยาน #${fav.bicycle_id}`}</strong>
                      <span className="muted small">
                        {bike?.station || 'สถานี -'} · เพิ่มเมื่อ {formatDateTime(fav.created_at)}
                      </span>
                    </span>
                    {editingId === fav.id ? null : (
                      <button
                        className="btn btn-sm btn-ghost"
                        type="button"
                        onClick={() => startEdit(fav)}
                      >
                        แก้ชื่อ
                      </button>
                    )}
                    <button
                      className="btn btn-sm btn-ghost"
                      type="button"
                      onClick={() => handleRemove(fav.id)}
                    >
                      ลบ
                    </button>
                  </li>
                </ul>
              </section>
            )
          })}
        </div>
      )}
    </div>
  )
}
