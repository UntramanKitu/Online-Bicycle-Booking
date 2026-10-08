import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, getApiError, assetUrl } from '../../api'
import { TICKET_CATEGORIES, TICKET_PRIORITIES, TICKET_STATUSES } from '../../constants'
import { useCurrentUser } from '../../context/currentUser'
import { formatDateTime } from '../../utils'

/** หน้าโปรไฟล์ — navbar เป็นแท็บ: ดูข้อมูล / แก้ชื่อ / แจ้งปัญหา / รายการโปรด / แจ้งซ่อม / รีวิว / คะแนน */
const TABS = [
  { id: 'info', label: '👤 ข้อมูลของฉัน' },
  { id: 'edit', label: '✏️ แก้ไขชื่อ/นามสกุล' },
  { id: 'tickets', label: '🎫 แจ้งปัญหา', key: 'tickets' },
  { id: 'favorites', label: '♥ รายการโปรด', key: 'favorites' },
  { id: 'maintenance', label: '🔧 แจ้งซ่อม', key: 'reports' },
  { id: 'reviews', label: '⭐ รีวิว', key: 'reviews' },
  { id: 'scores', label: '🏆 คะแนน', key: 'strikes' },
  { id: 'lost', label: '🎒 ของหาย', key: 'lost' },
]

const MAINT_STATUS = {
  pending: { label: 'รอดำเนินการ', cls: 'badge-warn' },
  in_progress: { label: 'กำลังซ่อม', cls: 'badge-active' },
  resolved: { label: 'ซ่อมเสร็จ', cls: 'badge-success' },
  cancelled: { label: 'ยกเลิก', cls: 'badge-muted' },
}

const MAX_POINTS = 12 // คอลัมน์ points เริ่มต้น 12 — ตรงกับ ScoresPage

const REASON_LABELS = {
  late_return: 'คืนรถสาย',
  damaged: 'ทำรถเสียหาย',
  lost: 'ทำรถสูญหาย',
  other: 'อื่นๆ',
  good_behavior: 'พฤติกรรมดี',
  no_violation_week: 'ไม่ทำผิดตลอดสัปดาห์',
}

const ACTION_LABELS = {
  warning: 'ตักเตือน',
  suspension: 'พักสิทธิ์',
  ban: 'ระงับการใช้งาน',
}


function levelOf(points) {
  if (points >= 10) return { label: 'ดีเยี่ยม', className: 'free' }
  if (points >= 6) return { label: 'พอใช้', className: 'warn' }
  return { label: 'มีความเสี่ยง', className: 'busy' }
}

export default function ProfilePage() {
  const { currentUser, usersLoading, userId, refreshUser } = useCurrentUser()
  // แท็บปัจจุบันเก็บใน URL (?tab=) — ให้ sidebar ใน Layout สลับเมนูได้พร้อมกัน
  const [searchParams] = useSearchParams()
  const tabParam = searchParams.get('tab') || 'info'
  const tab = TABS.some((t) => t.id === tabParam) ? tabParam : 'info'
  const [data, setData] = useState({ tickets: [], favorites: [], reports: [], reviews: [], strikes: [], bikes: [], lost: [] })
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({ first_name: '', last_name: '' })
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  // ฟอร์มสร้างรายการในแท็บ — ทำได้เลยในหน้าโปรไฟล์ ไม่ต้องกระโดดไปหน้าอื่น
  const [showTicketForm, setShowTicketForm] = useState(false)
  const [ticketForm, setTicketForm] = useState({ subject: '', description: '', category: 'bicycle_issue', priority: 'normal' })
  const [showMaintForm, setShowMaintForm] = useState(false)
  const [maintForm, setMaintForm] = useState({ bicycle_id: '', issue_type: '', description: '' })
  const [maintFiles, setMaintFiles] = useState([])
  const [showReviewForm, setShowReviewForm] = useState(false)
  const [reviewForm, setReviewForm] = useState({ bicycle_id: '', rating: 5, comment: '' })
  const [showLostForm, setShowLostForm] = useState(false)
  const [lostForm, setLostForm] = useState({ item_name: '', location: '', description: '', bicycle_id: '' })
  const [creating, setCreating] = useState(null) // 'tickets' | 'maintenance' | 'reviews' | 'lost'

  // โหลดข้อมูลของทุกแท็บครั้งเดียว — ตัวใดพังให้คิดเป็น [] ไม่พังทั้งหน้า
  useEffect(() => {
    if (usersLoading || !userId) return
    // เลื่อนไป task ถัดไป — กันกฎ react-hooks/set-state-in-effect
    const timer = window.setTimeout(async () => {
      const list = (p) => p.then((r) => (Array.isArray(r.data) ? r.data : [])).catch(() => [])
      const [tickets, favorites, reports, reviews, strikes, bikes, lost] = await Promise.all([
        list(api.get('/tickets', { params: { user_id: userId } })),
        list(api.get(`/favorites/user/${userId}`)),
        list(api.get(`/maintenance-reports/user/${userId}`)),
        list(api.get(`/reviews/user/${userId}`)),
        list(api.get(`/penalties/user/${userId}`)),
        list(api.get('/bicycles')),
        list(api.get(`/lost-items/user/${userId}`)),
      ])
      setData({ tickets, favorites, reports, reviews, strikes, bikes, lost })
      setLoading(false)
    }, 0)
    return () => window.clearTimeout(timer)
  }, [userId, usersLoading])

  // เติมค่าฟอร์มจากข้อมูลปัจจุบัน (ตอน mount และหลัง refreshUser)
  useEffect(() => {
    if (!currentUser) return
    // เลื่อนไป task ถัดไป — กันกฎ react-hooks/set-state-in-effect
    const timer = window.setTimeout(() => {
      setForm({ first_name: currentUser.first_name || '', last_name: currentUser.last_name || '' })
    }, 0)
    return () => window.clearTimeout(timer)
  }, [currentUser?.id, currentUser?.full_name]) // eslint-disable-line react-hooks/exhaustive-deps

  const bikeById = useMemo(() => new Map(data.bikes.map((b) => [b.id, b])), [data.bikes])

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    try {
      await api.patch('/auth/me', { first_name: form.first_name, last_name: form.last_name })
      await refreshUser() // ดึงชื่อใหม่เข้า context → header/ sidebar อัปเดตทันที
      setMessage({ type: 'success', text: 'บันทึกชื่อโปรไฟล์เรียบร้อย ✓' })
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setSaving(false)
    }
  }

  // ดึงรายการของแท็บเดียวกลับมาหลังสร้างสำเร็จ (ตัวใดพังไม่กระทบหน้า)
  async function refreshList(key, request) {
    try {
      const res = await request
      setData((d) => ({ ...d, [key]: Array.isArray(res.data) ? res.data : [] }))
    } catch {
      // ล้มเหลว → แสดงรายการเดิมต่อไป
    }
  }

  async function submitTicket(e) {
    e.preventDefault()
    setCreating('tickets')
    setMessage(null)
    try {
      await api.post('/tickets', { user_id: userId, ...ticketForm })
      setMessage({ type: 'success', text: 'ส่งคำร้องเรียบร้อย ✓' })
      setTicketForm({ subject: '', description: '', category: 'bicycle_issue', priority: 'normal' })
      setShowTicketForm(false)
      await refreshList('tickets', api.get('/tickets', { params: { user_id: userId } }))
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setCreating(null)
    }
  }

  async function submitMaintenance(e) {
    e.preventDefault()
    setCreating('maintenance')
    setMessage(null)
    try {
      // อัปโหลดรูปทีละไฟล์ก่อน (ถ้ามี) แล้วค่อยส่งรายงานพร้อม URL
      const imageUrls = []
      for (const file of maintFiles) {
        const fd = new FormData()
        fd.append('file', file)
        const up = await api.post('/upload', fd)
        imageUrls.push(up.data.url)
      }
      await api.post('/maintenance-reports', {
        bicycle_id: Number(maintForm.bicycle_id),
        reported_by: userId,
        issue_type: maintForm.issue_type,
        description: maintForm.description,
        images: imageUrls,
      })
      setMessage({ type: 'success', text: 'แจ้งซ่อมเรียบร้อย ✓' })
      setMaintForm({ bicycle_id: '', issue_type: '', description: '' })
      setMaintFiles([])
      setShowMaintForm(false)
      await refreshList('reports', api.get(`/maintenance-reports/user/${userId}`))
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setCreating(null)
    }
  }

  async function submitReview(e) {
    e.preventDefault()
    setCreating('reviews')
    setMessage(null)
    try {
      await api.post('/reviews', {
        user_id: userId,
        bicycle_id: Number(reviewForm.bicycle_id),
        reviewer_name: currentUser?.full_name || currentUser?.username || null,
        rating: Number(reviewForm.rating),
        comment: reviewForm.comment,
      })
      setMessage({ type: 'success', text: 'ส่งรีวิวเรียบร้อย ✓' })
      setReviewForm({ bicycle_id: '', rating: 5, comment: '' })
      setShowReviewForm(false)
      await refreshList('reviews', api.get(`/reviews/user/${userId}`))
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setCreating(null)
    }
  }

  // ---- แท็บของหาย: ของตัวเองเท่านั้น (ระบบรวมดูที่หน้า /lost-items) ----
  async function submitLost(e) {
    e.preventDefault()
    setCreating('lost')
    setMessage(null)
    try {
      await api.post('/lost-items', {
        user_id: userId,
        item_name: lostForm.item_name.trim(),
        location: lostForm.location.trim() || null,
        description: lostForm.description.trim() || null,
        bicycle_id: lostForm.bicycle_id ? Number(lostForm.bicycle_id) : null,
        status: 'lost',
      })
      setMessage({ type: 'success', text: 'แจ้งของหายเรียบร้อย ✓' })
      setLostForm({ item_name: '', location: '', description: '', bicycle_id: '' })
      setShowLostForm(false)
      await refreshList('lost', api.get(`/lost-items/user/${userId}`))
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setCreating(null)
    }
  }

  async function markLostFound(item) {
    setMessage(null)
    try {
      await api.put(`/lost-items/${item.id}`, { status: 'found', found_at: new Date().toISOString() })
      setMessage({ type: 'success', text: `อัปเดต "${item.item_name}" เป็นเจอแล้ว ✓` })
      await refreshList('lost', api.get(`/lost-items/user/${userId}`))
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    }
  }

  async function deleteLostItem(item) {
    if (!window.confirm('ลบรายการนี้หรือไม่?')) return
    setMessage(null)
    try {
      await api.delete(`/lost-items/${item.id}`)
      setMessage({ type: 'success', text: 'ลบรายการของหายเรียบร้อย ✓' })
      await refreshList('lost', api.get(`/lost-items/user/${userId}`))
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    }
  }

  if (usersLoading) return <p className="empty">กำลังโหลดข้อมูลโปรไฟล์...</p>
  if (!currentUser) return <p className="empty">กรุณาเข้าสู่ระบบก่อนใช้งาน</p>

  const displayName = currentUser.full_name || currentUser.username || 'ผู้ใช้'
  const initials = displayName.split(/\s+/).map((w) => w[0]).filter(Boolean).slice(0, 2).join('').toUpperCase()
  const isAdmin = currentUser.role === 'admin'
  const points = typeof currentUser.points === 'number' ? currentUser.points : MAX_POINTS
  const level = levelOf(points)

  return (
    <div className="page-section">
      <div className="section-head">
        <div>
          <h1 className="section-title">โปรไฟล์ของฉัน</h1>
          <p className="section-subtitle">ข้อมูลบัญชี, แก้ชื่อ/นามสกุล และภาพรวมการใช้งาน</p>
          <p classNmae=""></p>
        </div>
      </div>

      {message && (
        <div className={`alert ${message.type === 'error' ? 'alert-error' : 'alert-success'}`}>
          {message.text}
          <button className="alert-close" onClick={() => setMessage(null)}>×</button>
        </div>
      )}

      {loading ? (
        <p className="empty">กำลังโหลดข้อมูล...</p>
      ) : (
        <>
          {/* ---- แท็บ: ดูข้อมูลตัวเอง ---- */}
          {tab === 'info' && (
            <section className="panel profile-card">
              <div className="profile-avatar" aria-hidden="true">{initials || '👤'}</div>
              <div className="profile-info">
                <h2>{displayName}</h2>
                <p className="muted">@{currentUser.username} · {currentUser.email}</p>
                <div className="profile-badges">
                  <span className={`badge ${isAdmin ? 'badge-admin' : 'badge-user'}`}>
                    {isAdmin ? 'แอดมิน' : 'ผู้ใช้ทั่วไป'}
                  </span>
                  <span className={`badge ${currentUser.status === 'active' ? 'badge-user' : 'badge-admin'}`}>
                    {currentUser.status === 'active' ? 'บัญชีใช้งานได้' : 'บัญชีถูกระงับ'}
                  </span>
                  <span className="profile-points">⭐ {points} คะแนน</span>
                </div>
                {currentUser.date_joined && (
                  <p className="muted small">สมาชิกตั้งแต่ {formatDateTime(currentUser.date_joined)}</p>
                )}
              </div>
            </section>
          )}

          {/* ---- แท็บ: แก้ไขชื่อ/นามสกุล ---- */}
          {tab === 'edit' && (
            <form className="panel form-grid profile-form" onSubmit={handleSubmit}>
              <div className="field">
                <label htmlFor="profile-first-name">ชื่อ</label>
                <input
                  id="profile-first-name"
                  required
                  maxLength={150}
                  placeholder="เช่น สมชาย"
                  value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                />
              </div>
              <div className="field">
                <label htmlFor="profile-last-name">นามสกุล</label>
                <input
                  id="profile-last-name"
                  required
                  maxLength={150}
                  placeholder="เช่น ใจดี"
                  value={form.last_name}
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                />
              </div>
              <div className="form-actions">
                <button className="btn btn-primary" disabled={saving}>
                  {saving ? 'กำลังบันทึก...' : 'บันทึกชื่อ'}
                </button>
              </div>
              <p className="muted small profile-form-note">อีเมลและ username มาจากบัญชี Google จึงแก้ที่นี่ไม่ได้</p>
            </form>
          )}

          {/* ---- แท็บ: แจ้งปัญหา ---- */}
          {tab === 'tickets' && (
            <>
              <div className="section-head">
                <p className="muted">คำร้องแจ้งปัญหาของคุณ {data.tickets.length} รายการ</p>
                <button className="btn btn-sm btn-primary" type="button" onClick={() => setShowTicketForm((v) => !v)}>
                  {showTicketForm ? 'ปิดฟอร์ม' : '+ แจ้งปัญหาใหม่'}
                </button>
              </div>

              {showTicketForm && (
                <form className="panel form-grid" onSubmit={submitTicket}>
                  <div className="field">
                    <label>หัวข้อ *</label>
                    <input
                      required
                      maxLength={120}
                      placeholder="เช่น แอปค้างตอนกดจอง"
                      value={ticketForm.subject}
                      onChange={(e) => setTicketForm({ ...ticketForm, subject: e.target.value })}
                    />
                  </div>
                  <div className="field">
                    <label>รายละเอียด *</label>
                    <textarea
                      rows={3}
                      required
                      placeholder="อธิบายปัญหาที่พบ"
                      value={ticketForm.description}
                      onChange={(e) => setTicketForm({ ...ticketForm, description: e.target.value })}
                    />
                  </div>
                  <div className="field">
                    <label>หมวดหมู่</label>
                    <select value={ticketForm.category} onChange={(e) => setTicketForm({ ...ticketForm, category: e.target.value })}>
                      {Object.entries(TICKET_CATEGORIES).map(([value, meta]) => (
                        <option key={value} value={value}>{meta.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="field">
                    <label>ความเร่งด่วน</label>
                    <select value={ticketForm.priority} onChange={(e) => setTicketForm({ ...ticketForm, priority: e.target.value })}>
                      {Object.entries(TICKET_PRIORITIES).map(([value, meta]) => (
                        <option key={value} value={value}>{meta.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-actions">
                    <button className="btn btn-primary" disabled={creating === 'tickets'}>
                      {creating === 'tickets' ? 'กำลังส่ง...' : 'ส่งคำร้อง'}
                    </button>
                    <button className="btn btn-ghost" type="button" onClick={() => setShowTicketForm(false)}>ยกเลิก</button>
                  </div>
                </form>
              )}
              {data.tickets.length === 0 ? (
                <p className="empty">ยังไม่มีคำร้องแจ้งปัญหา</p>
              ) : (
                <div className="ticket-cards">
                  {data.tickets.map((t) => {
                    const st = TICKET_STATUSES[t.status] || { label: t.status, cls: 'badge-muted' }
                    const cat = TICKET_CATEGORIES[t.category]
                    return (
                      <article key={t.id} className="ticket-card">
                        <div className="ticket-card-head">
                          <h3>{t.subject}</h3>
                          <span className={`badge ${st.cls}`}>{st.label}</span>
                        </div>
                        <p className="muted small">{t.description}</p>
                        <div className="ticket-card-badges">
                          {cat && <span className={`badge ${cat.cls}`}>{cat.label}</span>}
                          <span className="muted small">แจ้งเมื่อ {formatDateTime(t.created_at)}</span>
                        </div>
                        {t.resolution_notes && <p><strong>ผลดำเนินการ:</strong> {t.resolution_notes}</p>}
                      </article>
                    )
                  })}
                </div>
              )}
            </>
          )}

          {/* ---- แท็บ: รายการโปรด ---- */}
          {tab === 'favorites' && (
            <>
              <div className="section-head">
                <p className="muted">จักรยานในรายการโปรด {data.favorites.length} คัน</p>
                <Link className="btn btn-sm btn-primary" to="/favorites">จัดการรายการโปรด</Link>
              </div>
              {data.favorites.length === 0 ? (
                <p className="empty">ยังไม่มีจักรยานในรายการโปรด — กด ♡ ที่หน้าจองจักรยานเพื่อเพิ่มได้เลย</p>
              ) : (
                <ul className="score-events">
                  {data.favorites.map((fav) => {
                    const bike = bikeById.get(fav.bicycle_id)
                    return (
                      <li key={fav.id}>
                        <span className="score-delta plus">♥</span>
                        <span className="score-reason">
                          <strong>{fav.nickname || (bike ? `${bike.code} · ${bike.model}` : `จักรยาน #${fav.bicycle_id}`)}</strong>
                          <span className="muted small">
                            {bike?.station || 'สถานี -'} · เพิ่มเมื่อ {formatDateTime(fav.created_at)}
                          </span>
                        </span>
                      </li>
                    )
                  })}
                </ul>
              )}
            </>
          )}

          {/* ---- แท็บ: แจ้งซ่อม ---- */}
          {tab === 'maintenance' && (
            <>
              <div className="section-head">
                <p className="muted">รายการแจ้งซ่อม {data.reports.length} รายการ</p>
                <button className="btn btn-sm btn-primary" type="button" onClick={() => setShowMaintForm((v) => !v)}>
                  {showMaintForm ? 'ปิดฟอร์ม' : '+ แจ้งซ่อมใหม่'}
                </button>
              </div>

              {showMaintForm && (
                <form className="panel form-grid" onSubmit={submitMaintenance}>
                  <div className="field">
                    <label>จักรยาน *</label>
                    <select required value={maintForm.bicycle_id} onChange={(e) => setMaintForm({ ...maintForm, bicycle_id: e.target.value })}>
                      <option value="">— เลือกจักรยาน —</option>
                      {data.bikes.map((b) => (
                        <option key={b.id} value={b.id}>{b.model} ({b.code}) · {b.station}</option>
                      ))}
                    </select>
                  </div>
                  <div className="field">
                    <label>ประเภทปัญหา *</label>
                    <input
                      required
                      maxLength={50}
                      placeholder="เช่น ยางแบน เบรกหลวม โซ่หลุด"
                      value={maintForm.issue_type}
                      onChange={(e) => setMaintForm({ ...maintForm, issue_type: e.target.value })}
                    />
                  </div>
                  <div className="field">
                    <label>รายละเอียด *</label>
                    <textarea
                      rows={3}
                      required
                      placeholder="อธิบายอาการที่พบ"
                      value={maintForm.description}
                      onChange={(e) => setMaintForm({ ...maintForm, description: e.target.value })}
                    />
                  </div>
                  <div className="field">
                    <label htmlFor="profile-report-files">รูปภาพประกอบ (ไม่บังคับ — สูงสุด 3 รูป)</label>
                    <input
                      id="profile-report-files"
                      type="file"
                      accept="image/*"
                      multiple
                      onChange={(e) => setMaintFiles(Array.from(e.target.files || []).slice(0, 3))}
                    />
                    {maintFiles.length > 0 && <span className="muted small">เลือกแล้ว {maintFiles.length} ไฟล์</span>}
                  </div>
                  <div className="form-actions">
                    <button className="btn btn-primary" disabled={creating === 'maintenance'}>
                      {creating === 'maintenance' ? 'กำลังส่ง...' : 'ส่งแจ้งซ่อม'}
                    </button>
                    <button className="btn btn-ghost" type="button" onClick={() => setShowMaintForm(false)}>ยกเลิก</button>
                  </div>
                </form>
              )}
              {data.reports.length === 0 ? (
                <p className="empty">ยังไม่มีรายการแจ้งซ่อม</p>
              ) : (
                <div className="ticket-cards">
                  {data.reports.map((r) => {
                    const meta = MAINT_STATUS[r.status] || { label: r.status, cls: 'badge-muted' }
                    const bike = bikeById.get(r.bicycle_id)
                    return (
                      <article key={r.id} className="ticket-card">
                        <div className="ticket-card-head">
                          <h3>{r.issue_type} · {bike ? `${bike.code} · ${bike.model}` : `จักรยาน #${r.bicycle_id}`}</h3>
                          <span className={`badge ${meta.cls}`}>{meta.label}</span>
                        </div>
                        <p className="muted small">{r.description}</p>
                        {(r.images || []).length > 0 && (
                          <div className="report-image-preview">
                            {r.images.map((src) => (
                              <a key={src} href={assetUrl(src)} target="_blank" rel="noreferrer" title="ดูรูปเต็ม">
                                <img src={assetUrl(src)} alt="รูปแจ้งซ่อม" />
                              </a>
                            ))}
                          </div>
                        )}
                        <div className="ticket-card-badges">
                          <span className="muted small">แจ้งเมื่อ {formatDateTime(r.reported_at)}</span>
                        </div>
                        {r.resolved_note && <p><strong>ผลซ่อม:</strong> {r.resolved_note}</p>}
                      </article>
                    )
                  })}
                </div>
              )}
            </>
          )}


          {/* ---- แท็บ: รีวิว ---- */}
          {tab === 'reviews' && (
            <>
              <div className="section-head">
                <p className="muted">
                  รีวิวของคุณ {data.reviews.length} รายการ
                  {data.reviews.length > 0 && (
                    <> · เฉลี่ย {(data.reviews.reduce((s, r) => s + (r.rating || 0), 0) / data.reviews.length).toFixed(1)} ⭐</>
                  )}
                </p>
                <button className="btn btn-sm btn-primary" type="button" onClick={() => setShowReviewForm((v) => !v)}>
                  {showReviewForm ? 'ปิดฟอร์ม' : '+ เขียนรีวิว'}
                </button>
              </div>

              {showReviewForm && (
                <form className="panel form-grid" onSubmit={submitReview}>
                  <div className="field">
                    <label>จักรยาน *</label>
                    <select required value={reviewForm.bicycle_id} onChange={(e) => setReviewForm({ ...reviewForm, bicycle_id: e.target.value })}>
                      <option value="">— เลือกจักรยาน —</option>
                      {data.bikes.map((b) => (
                        <option key={b.id} value={b.id}>{b.model} ({b.code}) · {b.station}</option>
                      ))}
                    </select>
                  </div>
                  <div className="field">
                    <label>คะแนน *</label>
                    <select value={reviewForm.rating} onChange={(e) => setReviewForm({ ...reviewForm, rating: e.target.value })}>
                      {[5, 4, 3, 2, 1].map((n) => (
                        <option key={n} value={n}>{'★'.repeat(n)} ({n})</option>
                      ))}
                    </select>
                  </div>
                  <div className="field">
                    <label>ความเห็น</label>
                    <textarea
                      rows={3}
                      placeholder="ชอบตรงไหน ควรปรับปรุงอะไร"
                      value={reviewForm.comment}
                      onChange={(e) => setReviewForm({ ...reviewForm, comment: e.target.value })}
                    />
                  </div>
                  <div className="form-actions">
                    <button className="btn btn-primary" disabled={creating === 'reviews'}>
                      {creating === 'reviews' ? 'กำลังส่ง...' : 'ส่งรีวิว'}
                    </button>
                    <button className="btn btn-ghost" type="button" onClick={() => setShowReviewForm(false)}>ยกเลิก</button>
                  </div>
                </form>
              )}
              {data.reviews.length === 0 ? (
                <p className="empty">ยังไม่มีรีวิว — กด "+ เขียนรีวิว" ด้านบนเพื่อเริ่มได้เลย</p>
              ) : (
                <div className="score-grid">
                  {data.reviews.map((rv) => {
                    const bike = bikeById.get(rv.bicycle_id)
                    return (
                      <section key={rv.id} className="ticket-card">
                        <header>
                          ⭐ {rv.rating}★ · {rv.rating >= 4 ? 'ประทับใจ' : rv.rating >= 3 ? 'พอใช้' : 'ยังไม่ประทับใจ'}
                        </header>
                        <ul className="score-events">
                          <li>
                            <span className="score-delta plus">{rv.rating}★</span>
                            <span className="score-reason">
                              <strong>{rv.comment || 'ไม่มีความเห็นเพิ่มเติม'}</strong>
                              <span className="muted small">
                                {rv.rating >= 4 ? 'ประทับใจ' : rv.rating >= 3 ? 'พอใช้' : 'ยังไม่ประทับใจ'} · {formatDateTime(rv.created_at)}
                              </span>
                            </span>
                          </li>
                        </ul>
                        <div className="ticket-card-badges">
                          <span className="muted small">
                            🚲 {bike ? `${bike.code} · ${bike.model}` : `จักรยาน #${rv.bicycle_id}`}
                          </span>
                        </div>
                      </section>
                    )
                  })}
                </div>
              )}
            </>
          )}

          {/* ---- แท็บ: ของหาย (เฉพาะของตัวเอง) ---- */}
          {tab === 'lost' && (
            <>
              <div className="section-head">
                <p className="muted">ของหายที่คุณแจ้ง {data.lost.length} รายการ · เห็นเฉพาะของตัวเอง</p>
                <button className="btn btn-sm btn-primary" type="button" onClick={() => setShowLostForm((v) => !v)}>
                  {showLostForm ? 'ปิดฟอร์ม' : '+ แจ้งของหาย'}
                </button>
              </div>

              {showLostForm && (
                <form className="panel form-grid" onSubmit={submitLost}>
                  <div className="field">
                    <label>สิ่งของที่หาย *</label>
                    <input
                      required
                      maxLength={100}
                      placeholder="เช่น ขวดน้ำ แจ็คเก็ต แว่นตา"
                      value={lostForm.item_name}
                      onChange={(e) => setLostForm({ ...lostForm, item_name: e.target.value })}
                    />
                  </div>
                  <div className="field">
                    <label>สถานที่ที่คาดว่าทำหาย</label>
                    <input
                      maxLength={200}
                      placeholder="เช่น ตะกร้าหน้ารถ ห้องสมุด"
                      value={lostForm.location}
                      onChange={(e) => setLostForm({ ...lostForm, location: e.target.value })}
                    />
                  </div>
                  <div className="field">
                    <label>รายละเอียดเพิ่มเติม</label>
                    <textarea
                      rows={3}
                      placeholder="สี ยี่ห้อ จุดสังเกต"
                      value={lostForm.description}
                      onChange={(e) => setLostForm({ ...lostForm, description: e.target.value })}
                    />
                  </div>
                  <div className="field">
                    <label>จักรยานที่ใช้ (ไม่บังคับ)</label>
                    <select
                      value={lostForm.bicycle_id}
                      onChange={(e) => setLostForm({ ...lostForm, bicycle_id: e.target.value })}
                    >
                      <option value="">— ไม่ระบุ —</option>
                      {data.bikes.map((b) => (
                        <option key={b.id} value={b.id}>{b.code} · {b.model}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-actions">
                    <button className="btn btn-primary" disabled={creating === 'lost'}>
                      {creating === 'lost' ? 'กำลังบันทึก...' : 'บันทึกการแจ้ง'}
                    </button>
                    <button className="btn btn-ghost" type="button" onClick={() => setShowLostForm(false)}>ยกเลิก</button>
                  </div>
                </form>
              )}

              {data.lost.length === 0 ? (
                <p className="empty">ยังไม่มีการแจ้งของหาย — กด "+ แจ้งของหาย" ด้านบนเพื่อเริ่มได้เลย</p>
              ) : (
                <div className="score-grid">
                  {data.lost.map((item) => {
                    const bike = bikeById.get(item.bicycle_id)
                    return (
                      <section key={item.id} className="ticket-card">
                        <header>
                          {item.item_name}{' '}
                          <span className={`status-pill ${item.status === 'found' ? 'free' : 'busy'}`}>
                            {item.status === 'found' ? '✅ เจอแล้ว' : '🔍 แจ้งหาย'}
                          </span>
                        </header>
                        <ul className="score-events">
                          <li>
                            <span className="score-delta minus">?</span>
                            <span className="score-reason">
                              <strong>{item.location || 'ไม่ระบุสถานที่'}</strong>
                              <span className="muted small">
                                {item.description || 'ไม่มีรายละเอียด'} · แจ้งเมื่อ {formatDateTime(item.created_at)}
                                {bike ? ` · ${bike.code}` : ''}
                              </span>
                            </span>
                          </li>
                        </ul>
                        <div className="confirm-actions">
                          {item.status !== 'found' && (
                            <button className="btn btn-sm btn-primary" type="button" onClick={() => markLostFound(item)}>
                              เจอแล้ว
                            </button>
                          )}
                          <button className="btn btn-sm btn-ghost" type="button" onClick={() => deleteLostItem(item)}>
                            ลบ
                          </button>
                        </div>
                      </section>
                    )
                  })}
                </div>
              )}
            </>
          )}

          {/* ---- แท็บ: คะแนน ---- */}
          {tab === 'scores' && (
            <>
              <div className="section-head">
                <p className="muted">คะแนนพฤติกรรมสะสม</p>
                <Link className="btn btn-sm btn-primary" to="/scores">ดูกติกาคะแนน & ประวัติทั้งหมด</Link>
              </div>
              <div className="score-hero">
                <div className="score-main">
                  <span className="score-number">{points}</span>
                  <span className="score-unit">/ {MAX_POINTS} คะแนน</span>
                  <span className={`status-pill ${level.className}`}>ระดับ: {level.label}</span>
                </div>
                <div className="score-side">
                  <p>ผู้ใช้: <strong>{displayName}</strong></p>
                  <p className="muted small">คะแนน &lt; 6 = ระบบจะจำกัดสิทธิ์การจองชั่วคราว</p>
                </div>
              </div>
              {data.strikes.length === 0 ? (
                <p className="empty">ยังไม่มีประวัติคะแนน — ทำได้ดีมาก! 🎉</p>
              ) : (
                <ul className="score-events">
                  {data.strikes.map((s) => {
                    const positive = s.reason === 'good_behavior' || s.reason === 'no_violation_week'
                    return (
                      <li key={s.id}>
                        <span className={`score-delta ${positive ? 'plus' : 'minus'}`}>
                          {positive ? `+${s.penalty_points}` : `-${s.penalty_points}`}
                        </span>
                        <span className="score-reason">
                          <strong>{REASON_LABELS[s.reason] || s.reason}</strong>
                          <span className="muted small">
                            {ACTION_LABELS[s.action] || s.action || ''}
                            {s.suspension_days ? ` ${s.suspension_days} วัน` : ''} · {formatDateTime(s.created_at)}
                          </span>
                        </span>
                        <span className={`status-pill ${positive ? 'free' : 'busy'}`}>
                          {s.completed ? 'ปิดเคสแล้ว' : positive ? 'รางวัล' : 'บทลงโทษ'}
                        </span>
                      </li>
                    )
                  })}
                </ul>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}


