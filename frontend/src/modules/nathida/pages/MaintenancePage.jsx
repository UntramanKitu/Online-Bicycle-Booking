import { useEffect, useState } from 'react'
import { api, getApiError } from '../../../api'
import { formatDateTime } from '../../../utils'
import { useCurrentUser } from '../../../context/currentUser'

const emptyForm = () => ({ bicycle_id: '', issue_type: '', description: '' })

const STATUS_META = {
  pending: { label: 'รอดำเนินการ', cls: 'badge-warn' },
  in_progress: { label: 'กำลังซ่อม', cls: 'badge-active' },
  resolved: { label: 'ซ่อมเสร็จ', cls: 'badge-success' },
  cancelled: { label: 'ยกเลิก', cls: 'badge-muted' },
}

export default function MaintenancePage() {
  const { userId, currentUser, usersLoading, isAdmin, getUserName } = useCurrentUser()
  const [reports, setReports] = useState([])
  const [bikes, setBikes] = useState([])
  // มุมมองของแอดมิน: mine = ของตัวเอง (default), all = รายงานแจ้งซ่อมทุกคน
  const [scope, setScope] = useState('mine')
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(emptyForm())
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)

  async function load(nextScope = scope) {
    setLoading(true)
    try {
      const [reportRes, bikeRes] = await Promise.all([
        nextScope === 'all' && isAdmin
          ? api.get('/maintenance-reports') // แอดมิน: รายงานทุกคน (endpoint tags=[ADMIN])
          : api.get(`/maintenance-reports/user/${userId}`),
        api.get('/bicycles'),
      ])
      setReports(reportRes.data)
      setBikes(bikeRes.data)
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (usersLoading || !userId) return
    const timer = window.setTimeout(() => load(scope), 0)
    return () => window.clearTimeout(timer)
  }, [userId, usersLoading, scope]) // eslint-disable-line react-hooks/exhaustive-deps

  function switchScope(next) {
    if (next === scope) return
    setMessage(null)
    setScope(next)
  }

  const getBikeName = (id) => {
    const found = bikes.find((b) => b.id === Number(id))
    return found ? `${found.model} (${found.code})` : `จักรยาน #${id}`
  }

  async function handleCreate(e) {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    try {
      await api.post('/maintenance-reports', {
        bicycle_id: Number(form.bicycle_id),
        reported_by: userId,
        issue_type: form.issue_type,
        description: form.description,
      })
      setMessage({ type: 'success', text: 'แจ้งซ่อมเรียบร้อย ✓' })
      setForm(emptyForm())
      setShowForm(false)
      load()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setSaving(false)
    }
  }

  if (!usersLoading && !currentUser) {
    return <p className="empty">กรุณาเข้าสู่ระบบด้วย Google ก่อนใช้งาน</p>
  }

  return (
    <div className="page-section">
      <div className="section-head">
        <div>
          <h1 className="section-title">แจ้งซ่อมจักรยาน</h1>
          <p className="section-subtitle">
            {scope === 'all'
              ? 'มุมมองแอดมิน — รายงานแจ้งซ่อมของผู้ใช้ทุกคนในระบบ'
              : 'แจ้งปัญหาตัวรถ — คุณจะเห็นเฉพาะรายการที่ตัวเองแจ้ง'}
          </p>
        </div>
        <div className="section-head-actions">
          {isAdmin && (
            <div className="tabs">
              <button className={`tab ${scope === 'mine' ? 'active' : ''}`} onClick={() => switchScope('mine')}>
                ของฉัน
              </button>
              <button className={`tab ${scope === 'all' ? 'active' : ''}`} onClick={() => switchScope('all')}>
                ทั้งระบบ
              </button>
            </div>
          )}
          <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
            {showForm ? 'ปิดฟอร์ม' : '+ แจ้งซ่อม'}
          </button>
        </div>
      </div>

      {message && (
        <div className={`alert ${message.type === 'error' ? 'alert-error' : 'alert-success'}`}>
          {message.text}
          <button className="alert-close" onClick={() => setMessage(null)}>×</button>
        </div>
      )}

      {showForm && (
        <form className="panel form-grid" onSubmit={handleCreate}>
          <div className="field">
            <label>จักรยาน *</label>
            <select
              required
              value={form.bicycle_id}
              onChange={(e) => setForm({ ...form, bicycle_id: e.target.value })}
            >
              <option value="">— เลือกจักรยาน —</option>
              {bikes.map((b) => (
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
              value={form.issue_type}
              onChange={(e) => setForm({ ...form, issue_type: e.target.value })}
            />
          </div>
          <div className="field">
            <label>รายละเอียด *</label>
            <textarea
              rows={3}
              required
              placeholder="อธิบายอาการที่พบ"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>
          <div className="form-actions">
            <button className="btn btn-primary" disabled={saving}>
              {saving ? 'กำลังส่ง...' : 'ส่งแจ้งซ่อม'}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>
              ยกเลิก
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <p className="empty">กำลังโหลดข้อมูล...</p>
      ) : reports.length === 0 ? (
        <p className="empty">ยังไม่มีรายการแจ้งซ่อม</p>
      ) : (
        <div className="ticket-cards">
          {reports.map((r) => {
            const meta = STATUS_META[r.status] || { label: r.status, cls: 'badge-muted' }
            return (
              <article className="ticket-card" key={r.id}>
                <div className="ticket-card-head">
                  <h3>{r.issue_type} · {getBikeName(r.bicycle_id)}</h3>
                  <span className={`badge ${meta.cls}`}>{meta.label}</span>
                </div>
                <p>{r.description}</p>
                <div className="ticket-card-badges">
                  {scope === 'all' && <span className="badge badge-muted">ผู้แจ้ง {getUserName(r.reported_by)}</span>}
                  <span className="muted small">แจ้งเมื่อ {formatDateTime(r.reported_at)}</span>
                </div>
                {r.resolved_note && <p><strong>ผลซ่อม:</strong> {r.resolved_note}</p>}
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}
