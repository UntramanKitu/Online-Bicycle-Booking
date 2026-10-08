import { useEffect, useMemo, useState } from 'react'
import { api, getApiError } from '../../../api'
import { formatDateTime } from '../../../utils'
import { useCurrentUser } from '../../../context/currentUser'
import '../akeapon.css'

const EMPTY_FORM = { item_name: '', location: '', description: '', bicycle_id: '' }

const STATUS_LABELS = {
  lost: '🔍 แจ้งหาย',
  found: '✅ เจอแล้ว',
}

// ระบบของหาย — หน้านี้ (เข้าจากหน้า Home) แสดง "ทั้งระบบ" ทุกคน · ส่วนของตัวเองดูที่แท็บ 🎒 ของหายในโปรไฟล์
export default function LostItemsPage() {
  const { userId, usersLoading, getUserName, isAdmin } = useCurrentUser()
  const [items, setItems] = useState([])
  const [bikes, setBikes] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)

  async function load() {
    setLoading(true)
    try {
      const [itemRes, bikeRes] = await Promise.all([
        api.get('/lost-items'), // ทั้งระบบ (ทุกคน) — ของตัวเองอยู่ที่แท็บในโปรไฟล์
        api.get('/bicycles'),
      ])
      setItems(itemRes.data || [])
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
  }, [userId, usersLoading])

  const bikeById = useMemo(() => new Map(bikes.map((b) => [b.id, b])), [bikes])

  async function handleCreate(e) {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    try {
      await api.post('/lost-items', {
        user_id: userId,
        item_name: form.item_name.trim(),
        location: form.location.trim() || null,
        description: form.description.trim() || null,
        bicycle_id: form.bicycle_id ? Number(form.bicycle_id) : null,
        status: 'lost',
      })
      setMessage({ type: 'success', text: 'แจ้งของหายเรียบร้อย ✓' })
      setForm(EMPTY_FORM)
      setShowForm(false)
      load()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setSaving(false)
    }
  }

  async function markFound(item) {
    setMessage(null)
    try {
      await api.put(`/lost-items/${item.id}`, {
        status: 'found',
        found_at: new Date().toISOString(),
      })
      setMessage({ type: 'success', text: `อัปเดต "${item.item_name}" เป็นเจอแล้ว ✓` })
      load()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('ลบรายการนี้หรือไม่?')) return
    setMessage(null)
    try {
      await api.delete(`/lost-items/${id}`)
      setItems((prev) => prev.filter((i) => i.id !== id))
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
          <h1 className="section-title">ของหาย</h1>
          <p className="section-subtitle">ของหายทั้งระบบ — ดูได้ทุกคน แก้ไขได้เฉพาะของตัวเอง (ของคุณอยู่ที่แท็บโปรไฟล์ด้วย)</p>
        </div>
        <button className="btn btn-primary" type="button" onClick={() => setShowForm((v) => !v)}>
          {showForm ? '× ปิดฟอร์ม' : '+ แจ้งของหาย'}
        </button>
      </div>

      {message && (
        <div className={`alert ${message.type === 'error' ? 'alert-error' : 'alert-success'}`}>
          {message.text}
        </div>
      )}

      {showForm && (
        <form className="ticket-card" onSubmit={handleCreate}>
          <header>แจ้งของหายใหม่</header>
          <div className="field">
            <label htmlFor="lost-item">สิ่งของที่หาย *</label>
            <input
              id="lost-item"
              value={form.item_name}
              onChange={(e) => setForm({ ...form, item_name: e.target.value })}
              placeholder="เช่น ขวดน้ำ แจ็คเก็ต แว่นตา"
              required
              maxLength={100}
            />
          </div>
          <div className="field">
            <label htmlFor="lost-bike">จักรยานที่ใช้ (ไม่บังคับ)</label>
            <select
              id="lost-bike"
              value={form.bicycle_id}
              onChange={(e) => setForm({ ...form, bicycle_id: e.target.value })}
            >
              <option value="">— ไม่ระบุ —</option>
              {bikes.map((b) => (
                <option key={b.id} value={b.id}>{b.code} · {b.model}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="lost-loc">สถานที่ที่คาดว่าทำหาย</label>
            <input
              id="lost-loc"
              value={form.location}
              onChange={(e) => setForm({ ...form, location: e.target.value })}
              placeholder="เช่น ตะกร้าหน้ารถ ห้องสมุด"
              maxLength={200}
            />
          </div>
          <div className="field">
            <label htmlFor="lost-desc">รายละเอียดเพิ่มเติม</label>
            <textarea
              id="lost-desc"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="สี ยี่ห้อ จุดสังเกต"
            />
          </div>
          <div className="confirm-actions">
            <button className="btn btn-primary" type="submit" disabled={saving}>
              {saving ? 'กำลังบันทึก...' : 'บันทึกการแจ้ง'}
            </button>
            <button className="btn btn-ghost" type="button" onClick={() => setShowForm(false)}>
              ยกเลิก
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <p className="empty">กำลังโหลดรายการ...</p>
      ) : items.length === 0 ? (
        <p className="empty">ยังไม่มีการแจ้งของหาย</p>
      ) : (
        <div className="score-grid">
          {items.map((item) => (
            <section key={item.id} className="ticket-card">
              <header>
                {item.item_name}{' '}
                <span className={`status-pill ${item.status === 'found' ? 'free' : 'busy'}`}>
                  {STATUS_LABELS[item.status] || item.status}
                </span>
              </header>
              <ul className="score-events">
                <li>
                  <span className="score-delta minus">?</span>
                  <span className="score-reason">
                    <strong>{item.location || 'ไม่ระบุสถานที่'}</strong>
                    <span className="muted small">
                      {item.description || 'ไม่มีรายละเอียด'} · แจ้งเมื่อ {formatDateTime(item.created_at)} · ผู้แจ้ง {getUserName(item.user_id)}
                      {item.bicycle_id && bikeById.get(item.bicycle_id)
                        ? ` · ${bikeById.get(item.bicycle_id).code}`
                        : ''}
                    </span>
                  </span>
                </li>
              </ul>
              {(Number(item.user_id) === Number(userId) || isAdmin) && (
                <div className="confirm-actions">
                  {item.status !== 'found' && (
                    <button className="btn btn-sm btn-primary" type="button" onClick={() => markFound(item)}>
                      เจอแล้ว
                    </button>
                  )}
                  <button className="btn btn-sm btn-ghost" type="button" onClick={() => handleDelete(item.id)}>
                    ลบ
                  </button>
                </div>
              )}
            </section>
          ))}
        </div>
      )}
    </div>
  )
}
