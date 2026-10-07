import { useEffect, useState } from 'react'
import { api, getApiError } from '../../../api'
import { TICKET_CATEGORIES, TICKET_PRIORITIES, TICKET_STATUSES } from '../../../constants'
import { formatDateTime } from '../../../utils'
import { useCurrentUser } from '../../../context/currentUser'

const emptyForm = () => ({
  subject: '',
  description: '',
  category: 'bicycle_issue',
  priority: 'normal',
})

const STATUS_TRANSITIONS = {
  open:        ['in_progress', 'closed'],
  in_progress: ['resolved', 'closed'],
  resolved:    ['closed', 'reopened'],
  closed:      ['reopened'],
  reopened:    ['in_progress', 'closed'],
}

const STATUS_LABELS = {
  open: 'เปิดเคส',
  in_progress: 'กำลังดำเนินการ',
  resolved: '✅ แก้ไขเสร็จแล้ว',
  closed: '🔒 ปิดเคส',
  reopened: 'เปิดใหม่',
}

export default function TicketsPage() {
  const { userId, currentUser, usersLoading, isAdmin, getUserName } = useCurrentUser()
  const [tickets, setTickets] = useState([])
  const [scope, setScope] = useState('mine')
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(emptyForm())
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [activeId, setActiveId] = useState(null)
  const [bulkDeleting, setBulkDeleting] = useState(false)
  const [filterStatus, setFilterStatus] = useState('all')

  async function load(nextScope = scope) {
    setLoading(true)
    try {
      const res = nextScope === 'all' && isAdmin
        ? await api.get('/tickets')
        : await api.get('/tickets', { params: { user_id: userId } })
      setTickets(res.data)
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
    setFilterStatus('all')
    setScope(next)
  }

  async function handleCreate(e) {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    try {
      await api.post('/tickets', {
        user_id: userId,
        subject: form.subject,
        description: form.description,
        category: form.category,
        priority: form.priority,
      })
      setMessage({ type: 'success', text: 'ส่งคำร้องเรียบร้อย ✓' })
      setForm(emptyForm())
      setShowForm(false)
      load()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('ลบคำร้องนี้หรือไม่?')) return
    setMessage(null)
    try {
      await api.delete(`/tickets/${id}`, { params: { user_id: userId } })
      load()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    }
  }

  // ===== Admin actions =====
  async function adminChangeStatus(ticket, newStatus) {
    const note = newStatus === 'resolved' || newStatus === 'closed'
      ? window.prompt(`หมายเหตุการ ${STATUS_LABELS[newStatus]} (กด OK เพื่อข้าม):`, ticket.resolution_notes || '')
      : null
    if (note === null && (newStatus === 'resolved' || newStatus === 'closed')) {
      // user กด Cancel prompt — ยกเลิก
      // แต่ถ้า note เป็น "" (กด OK แล้วเว้นว่าง) ก็ยังดำเนินการต่อ
    }
    try {
      const res = await api.patch(`/admin/tickets/${ticket.id}/status`, {
        status: newStatus,
        resolution_notes: note ?? undefined,
      })
      setTickets((prev) => prev.map((t) => (t.id === res.data.id ? res.data : t)))
      setMessage({ type: 'success', text: `เปลี่ยนสถานะเป็น "${STATUS_LABELS[newStatus]}" แล้ว ✓` })
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    }
  }

  async function adminDeleteTicket(ticket) {
    if (!window.confirm(`ลบคำร้อง "${ticket.subject}" (ID ${ticket.id}) หรือไม่?\nการลบนี้ไม่สามารถย้อนกลับได้`)) return
    try {
      await api.delete(`/admin/tickets/${ticket.id}`)
      setTickets((prev) => prev.filter((t) => t.id !== ticket.id))
      setMessage({ type: 'success', text: 'ลบคำร้องเรียบร้อย ✓' })
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    }
  }

  async function adminBulkDelete(status) {
    const label = STATUS_LABELS[status] || status
    const count = tickets.filter((t) => t.status === status).length
    if (count === 0) { setMessage({ type: 'error', text: `ไม่มีเคสที่มีสถานะ "${label}"` }); return }
    if (!window.confirm(`ลบเคส "${label}" ทั้งหมด ${count} รายการ?\nการลบนี้ไม่สามารถย้อนกลับได้`)) return
    setBulkDeleting(true)
    try {
      const res = await api.delete('/admin/tickets', { params: { status } })
      setMessage({ type: 'success', text: `ลบ ${res.data.deleted} เคสเรียบร้อย ✓` })
      load()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setBulkDeleting(false)
    }
  }

  const summary = tickets.reduce((acc, t) => {
    acc[t.status] = (acc[t.status] || 0) + 1
    return acc
  }, {})

  const displayTickets = filterStatus === 'all'
    ? tickets
    : tickets.filter((t) => t.status === filterStatus)

  if (!usersLoading && !currentUser) {
    return <p className="empty">กรุณาเข้าสู่ระบบด้วย Google ก่อนใช้งาน</p>
  }

  return (
    <div className="page-section">
      <div className="section-head">
        <div>
          <h1 className="section-title">แจ้งปัญหา</h1>
          <p className="section-subtitle">
            {scope === 'all'
              ? 'มุมมองแอดมิน — คำร้องแจ้งปัญหาของผู้ใช้ทุกคนในระบบ'
              : 'แจ้งปัญหาการใช้งาน เช่น แอปค้าง หรือพบปัญหาที่จุดจอด เพื่อให้เจ้าหน้าที่ตรวจสอบและแก้ไข'}
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
            {showForm ? 'ปิดฟอร์ม' : '+ แจ้งปัญหา'}
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
            <label>ผู้แจ้ง</label>
            <input type="text" value={getUserName(userId)} disabled />
          </div>
          <div className="field">
            <label>หัวข้อ *</label>
            <input
              required
              placeholder="เช่น เบาะจักรยานไม่แน่น"
              value={form.subject}
              onChange={(e) => setForm({ ...form, subject: e.target.value })}
            />
          </div>
          <div className="field">
            <label>หมวดหมู่ *</label>
            <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
              {Object.entries(TICKET_CATEGORIES).map(([v, m]) => (
                <option key={v} value={v}>{m.label}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>ความเร่งด่วน</label>
            <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
              {Object.entries(TICKET_PRIORITIES).map(([v, m]) => (
                <option key={v} value={v}>{m.label}</option>
              ))}
            </select>
          </div>
          <div className="field field-wide">
            <label>รายละเอียด *</label>
            <textarea
              rows={3}
              required
              placeholder="อธิบายปัญหาที่พบ (เช่น แอปค้างตอนกดจอง จักรยานล้อแบน)"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>
          <div className="form-actions">
            <button className="btn btn-primary" disabled={saving}>
              {saving ? 'กำลังส่ง...' : 'ส่งคำร้อง'}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>
              ยกเลิก
            </button>
          </div>
        </form>
      )}

      {/* Admin bulk-delete toolbar */}
      {isAdmin && scope === 'all' && (
        <div className="admin-ticket-toolbar">
          <span className="admin-toolbar-label">🛡️ เครื่องมือแอดมิน:</span>
          <button
            id="admin-bulk-close-btn"
            className="btn btn-sm btn-ghost"
            disabled={bulkDeleting || (summary['closed'] || 0) === 0}
            onClick={() => adminBulkDelete('closed')}
            title={`ลบเคสปิดทั้งหมด (${summary['closed'] || 0} รายการ)`}
          >
            🗑️ ลบเคสปิด ({summary['closed'] || 0})
          </button>
          <button
            id="admin-bulk-resolved-btn"
            className="btn btn-sm btn-ghost"
            disabled={bulkDeleting || (summary['resolved'] || 0) === 0}
            onClick={() => adminBulkDelete('resolved')}
            title={`ลบเคสแก้ไขเสร็จทั้งหมด (${summary['resolved'] || 0} รายการ)`}
          >
            🗑️ ลบเคสเสร็จ ({summary['resolved'] || 0})
          </button>
        </div>
      )}

      {/* Status summary + filter */}
      <div className="ticket-status-bar">
        <button
          className={`tab ${filterStatus === 'all' ? 'active' : ''}`}
          onClick={() => setFilterStatus('all')}
        >
          ทั้งหมด ({tickets.length})
        </button>
        {Object.entries(TICKET_STATUSES).map(([v, m]) => (
          <button
            key={v}
            className={`tab ${filterStatus === v ? 'active' : ''}`}
            onClick={() => setFilterStatus(filterStatus === v ? 'all' : v)}
          >
            <span className={`badge ${m.cls}`}>{m.label}</span>
            <span>{summary[v] || 0}</span>
          </button>
        ))}
      </div>

      {loading ? (
        <p className="empty">กำลังโหลดข้อมูล...</p>
      ) : displayTickets.length === 0 ? (
        <p className="empty">ไม่มีคำร้องที่ตรงกับตัวกรอง</p>
      ) : (
        <div className="ticket-cards">
          {displayTickets.map((t) => {
            const catMeta = TICKET_CATEGORIES[t.category] || { label: t.category, cls: 'badge-muted' }
            const priMeta = TICKET_PRIORITIES[t.priority] || { label: t.priority, cls: 'badge-muted' }
            const statMeta = TICKET_STATUSES[t.status] || { label: t.status, cls: 'badge-muted' }
            const isActive = activeId === t.id
            const nextStatuses = isAdmin ? (STATUS_TRANSITIONS[t.status] || []) : []
            return (
              <article className={`ticket-card status-${t.status}`} key={t.id}>
                <div className="ticket-card-head">
                  <h3>{t.subject}</h3>
                  <span className={`badge ${statMeta.cls}`}>{statMeta.label}</span>
                </div>
                <div className="ticket-card-badges">
                  {scope === 'all' && <span className="badge badge-muted">ผู้แจ้ง {getUserName(t.user_id)}</span>}
                  <span className={`badge ${catMeta.cls}`}>{catMeta.label}</span>
                  <span className={`badge ${priMeta.cls}`}>เร่งด่วน: {priMeta.label}</span>
                  <span className="muted small">{formatDateTime(t.created_at)}</span>
                </div>
                {isActive && <TicketDetail ticket={t} getUserName={getUserName} />}
                <div className="ticket-card-actions">
                  <button
                    className="btn btn-sm btn-ghost"
                    onClick={() => setActiveId(isActive ? null : t.id)}
                  >
                    {isActive ? 'ซ่อนรายละเอียด' : 'ดูรายละเอียด'}
                  </button>

                  {/* Admin: เปลี่ยนสถานะ */}
                  {isAdmin && nextStatuses.length > 0 && (
                    <div className="admin-status-actions">
                      {nextStatuses.map((s) => (
                        <button
                          key={s}
                          id={`admin-ticket-${t.id}-to-${s}`}
                          className={`btn btn-sm ${s === 'closed' || s === 'resolved' ? 'btn-primary' : 'btn-ghost'}`}
                          onClick={() => adminChangeStatus(t, s)}
                        >
                          {STATUS_LABELS[s]}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Admin: ลบทันที */}
                  {isAdmin && (
                    <button
                      id={`admin-del-ticket-${t.id}`}
                      className="btn btn-danger-sm"
                      onClick={() => adminDeleteTicket(t)}
                    >
                      🗑️ ลบ
                    </button>
                  )}

                  {/* เจ้าของ: ลบของตัวเอง (เฉพาะเคสปิด) */}
                  {!isAdmin && Number(t.user_id) === Number(userId) && t.status === 'closed' && (
                    <button className="btn btn-danger-sm" onClick={() => handleDelete(t.id)}>
                      ลบคำร้อง
                    </button>
                  )}
                </div>
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}

function TicketDetail({ ticket, getUserName }) {
  return (
    <div className="ticket-detail">
      <p><strong>รายละเอียด:</strong> {ticket.description}</p>
      {ticket.assigned_to != null && (
        <p><strong>เจ้าหน้าที่ที่รับผิดชอบ:</strong> {getUserName(ticket.assigned_to)}</p>
      )}
      {ticket.resolved_at && (
        <p><strong>แก้ไขเสร็จเมื่อ:</strong> {new Date(ticket.resolved_at).toLocaleString('th-TH')}</p>
      )}
      {ticket.resolution_notes && (
        <p><strong>ผลการแก้ไข:</strong> {ticket.resolution_notes}</p>
      )}
    </div>
  )
}