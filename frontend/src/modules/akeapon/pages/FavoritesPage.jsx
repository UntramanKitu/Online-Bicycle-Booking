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
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [bikeId, setBikeId] = useState('')
  const [nickname, setNickname] = useState('')

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
  const favoritedIds = useMemo(() => new Set(favorites.map((f) => f.bicycle_id)), [favorites])
  const availableBikes = bikes.filter((b) => !favoritedIds.has(b.id))

  async function handleAdd(e) {
    e.preventDefault()
    if (!bikeId) return
    setSaving(true)
    setMessage(null)
    try {
      await api.post('/favorites', {
        user_id: userId,
        target_type: 'bicycle',
        bicycle_id: Number(bikeId),
        nickname: nickname.trim() || null,
      })
      setMessage({ type: 'success', text: 'เพิ่มรายการโปรดแล้ว ♥' })
      setBikeId('')
      setNickname('')
      load()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setSaving(false)
    }
  }

  async function handleRemove(id) {
    setMessage(null)
    try {
      await api.delete(`/favorites/${id}`)
      setFavorites((prev) => prev.filter((f) => f.id !== id))
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
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

      <form className="ticket-card fav-add-form" onSubmit={handleAdd}>
        <header>เพิ่มจักรยานโปรด</header>
        <div className="field">
          <label htmlFor="fav-bike">เลือกจักรยาน</label>
          <select
            id="fav-bike"
            value={bikeId}
            onChange={(e) => setBikeId(e.target.value)}
            required
          >
            <option value="">— เลือกจักรยาน —</option>
            {availableBikes.map((b) => (
              <option key={b.id} value={b.id}>
                {b.code} · {b.model} · {b.station}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="fav-nick">ชื่อเรียก (ไม่บังคับ)</label>
          <input
            id="fav-nick"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            placeholder="เช่น คันประจำ, คันเร็ว"
            maxLength={100}
          />
        </div>
        <button className="btn btn-primary" type="submit" disabled={saving || !bikeId}>
          {saving ? 'กำลังบันทึก...' : '♥ เพิ่มรายการโปรด'}
        </button>
      </form>

      {loading ? (
        <p className="empty">กำลังโหลดรายการโปรด...</p>
      ) : favorites.length === 0 ? (
        <p className="empty">ยังไม่มีจักรยานในรายการโปรด — เลือกด้านบนแล้วกดเพิ่มได้เลย</p>
      ) : (
        <div className="score-grid">
          {favorites.map((fav) => {
            const bike = bikeById.get(fav.bicycle_id)
            return (
              <section key={fav.id} className="ticket-card">
                <header>
                  {fav.nickname || bike?.model || `จักรยาน #${fav.bicycle_id}`}
                </header>
                <ul className="score-events">
                  <li>
                    <span className="score-delta plus">♥</span>
                    <span className="score-reason">
                      <strong>{bike ? `${bike.code} · ${bike.model}` : `จักรยาน #${fav.bicycle_id}`}</strong>
                      <span className="muted small">
                        {bike?.station || 'สถานี -'} · เพิ่มเมื่อ {formatDateTime(fav.created_at)}
                      </span>
                    </span>
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
