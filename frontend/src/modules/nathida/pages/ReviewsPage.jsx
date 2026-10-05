import { useEffect, useState } from 'react'
import { api, getApiError } from '../../../api'
import { formatDateTime } from '../../../utils'
import { useCurrentUser } from '../../../context/currentUser'
import Stars from '../../../components/Stars'

const emptyForm = () => ({ bicycle_id: '', rating: 5, comment: '' })

function formatRating(value) {
  if (value == null) return '-'
  const num = Number(value)
  return Number.isInteger(num) ? String(num) : num.toFixed(1)
}

export default function ReviewsPage() {
  const { userId, currentUser, usersLoading } = useCurrentUser()
  const [bikes, setBikes] = useState([])
  const [selectedBike, setSelectedBike] = useState('')
  const [reviews, setReviews] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(emptyForm())
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)

  async function loadBikes() {
    try {
      const res = await api.get('/bicycles')
      setBikes(res.data)
      if (!selectedBike && res.data.length > 0) setSelectedBike(String(res.data[0].id))
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    }
  }

  async function loadReviews(bikeId) {
    if (!bikeId) return
    setLoading(true)
    try {
      const [listRes, sumRes] = await Promise.all([
        api.get(`/reviews/bicycle/${bikeId}`),
        api.get(`/reviews/bicycle/${bikeId}/summary`),
      ])
      setReviews(listRes.data)
      setSummary(sumRes.data)
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (usersLoading || !userId) return
    const timer = window.setTimeout(loadBikes, 0)
    return () => window.clearTimeout(timer)
  }, [userId, usersLoading]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (usersLoading || !userId || !selectedBike) return
    const timer = window.setTimeout(() => loadReviews(selectedBike), 0)
    return () => window.clearTimeout(timer)
  }, [selectedBike, userId, usersLoading])

  async function handleCreate(e) {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    try {
      await api.post('/reviews', {
        user_id: userId,
        bicycle_id: Number(form.bicycle_id || selectedBike),
        reviewer_name: currentUser?.full_name || currentUser?.username || null,
        rating: Number(form.rating),
        comment: form.comment,
      })
      setMessage({ type: 'success', text: 'ส่งรีวิวเรียบร้อย' })
      setForm(emptyForm())
      setShowForm(false)
      loadReviews(form.bicycle_id || selectedBike)
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setSaving(false)
    }
  }

  if (!usersLoading && !currentUser) {
    return <p className="empty">กรุณาเข้าสู่ระบบด้วย Google ก่อนใช้งาน</p>
  }

  return <ReviewsView
    summary={summary}
    message={message}
    setMessage={setMessage}
    bikes={bikes}
    selectedBike={selectedBike}
    setSelectedBike={setSelectedBike}
    showForm={showForm}
    setShowForm={setShowForm}
    setForm={setForm}
    form={form}
    saving={saving}
    handleCreate={handleCreate}
    loading={loading}
    reviews={reviews}
  />
}

function ReviewsView(props) {
  const { summary, message, setMessage, bikes, selectedBike, setSelectedBike } = props
  const { showForm, setShowForm, setForm, form, saving, handleCreate, loading, reviews } = props
  return (
    <div className="page-section">
      <div className="section-head">
        <div>
          <h1 className="section-title">รีวิว & ให้คะแนน</h1>
          <p className="section-subtitle">
            {summary
              ? `คะแนนเฉลี่ย ${summary.average_rating} จาก ${summary.review_count} รีวิว`
              : 'เลือกจักรยานเพื่อดูรีวิว'}
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => { setForm((f) => ({ ...f, bicycle_id: selectedBike })); setShowForm((v) => !v) }}>
          {showForm ? 'ปิดฟอร์ม' : '+ เขียนรีวิว'}
        </button>
      </div>

      {message && (
        <div className={`alert ${message.type === 'error' ? 'alert-error' : 'alert-success'}`}>
          {message.text}
          <button className="alert-close" onClick={() => setMessage(null)}>×</button>
        </div>
      )}

      <div className="field" style={{ maxWidth: 360 }}>
        <label>จักรยาน</label>
        <select value={selectedBike} onChange={(e) => setSelectedBike(e.target.value)}>
          {bikes.map((b) => (
            <option key={b.id} value={b.id}>{b.model} ({b.code})</option>
          ))}
        </select>
      </div>

      {showForm && (
        <form className="panel form-grid" onSubmit={handleCreate}>
          <div className="field">
            <label>คะแนน (1-5 ดาว กดครึ่งดาวได้) *</label>
            <Stars value={Number(form.rating)} allowHalf onPick={(s) => setForm({ ...form, rating: s })} />
          </div>
          <div className="field">
            <label>ความคิดเห็น *</label>
            <textarea
              rows={3}
              required
              placeholder="เล่าประสบการณ์ใช้งานจักรยานคันนี้"
              value={form.comment}
              onChange={(e) => setForm({ ...form, comment: e.target.value })}
            />
          </div>
          <div className="form-actions">
            <button className="btn btn-primary" disabled={saving}>
              {saving ? 'กำลังส่ง...' : 'ส่งรีวิว'}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>
              ยกเลิก
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <p className="empty">กำลังโหลดข้อมูล...</p>
      ) : reviews.length === 0 ? (
        <p className="empty">ยังไม่มีรีวิวสำหรับจักรยานคันนี้</p>
      ) : (
        <div className="ticket-cards">
          {reviews.map((r) => (
            <article className="ticket-card" key={r.id}>
              <div className="ticket-card-head">
                <h3>{r.reviewer_name || 'ผู้ใช้'}</h3>
                <span className="badge badge-warn">{'★'.repeat(Math.round(Number(r.rating)))} ({formatRating(r.rating)}/5)</span>
              </div>
              <p>{r.comment}</p>
              <div className="ticket-card-badges">
                <span className="muted small">{formatDateTime(r.created_at)}</span>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
