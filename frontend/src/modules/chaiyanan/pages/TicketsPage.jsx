import { useEffect, useState } from 'react'
import { api, getApiError } from '../../../api'
import { TICKET_CATEGORIES, TICKET_PRIORITIES, TICKET_STATUSES } from '../../../constants'
import { formatDateTime } from '../../../utils'
import { useCurrentUser } from '../../../context/CurrentUserContext'

const emptyForm = () => ({
  subject: '',
  description: '',
  category: 'bicycle_issue',
  priority: 'normal',
})

export default function TicketsPage() {
  const { userId } = useCurrentUser()
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(emptyForm())
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [activeId, setActiveId] = useState(null)

  async function load() {
    setLoading(true)
    try {
      const res = await api.get('/tickets')
      setTickets(res.data)
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(load, 0)
    return () => window.clearTimeout(timer)
  }, [])

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

  async function handleUpdate(id, payload) {
    setMessage(null)
    try {
      await api.put(`/tickets/${id}`, payload)
      load()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('ลบคำร้องนี้หรือไม่?')) return
    setMessage(null)
    try {
      await api.delete(`/tickets/${id}`)
      load()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    }
  }

  const summary = tickets.reduce((acc, t) => {
    acc[t.status] = (acc[t.status] || 0) + 1
    return acc
  }, {})

  return (
    <div className="page-section">
      <div className="section-head">
        <div>
          <h1 className="section-title">Support Tickets</h1>
          <p className="section-subtitle">
            ระบบรับแจ้งปัญหาการใช้งาน เช่น แอปค้าง หรือพบปัญหาที่จุดจอด เพื่อให้เจ้าหน้าที่ตรวจสอบและแก้ไข
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? 'ปิดฟอร์ม' : '+ แจ้งปัญหา'}
        </button>
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
            <label>ผู้ใช้ (user_id)</label>
            <input type="number" value={userId} disabled />
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

      <div className="tabs">
        {Object.entries(TICKET_STATUSES).map(([v, m]) => (
          <span key={v} className={`badge ${m.cls}`}>
            {m.label}: {summary[v] || 0}
          </span>
        ))}
      </div>

      <div className="panel">
        {loading ? (
          <p className="empty">กำลังโหลดข้อมูล...</p>
        ) : tickets.length === 0 ? (
          <p className="empty">ยังไม่มีคำร้องแจ้งปัญหา</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>#</th>
                <th>ผู้ใช้</th>
                <th>หัวข้อ</th>
                <th>หมวดหมู่</th>
                <th>เร่งด่วน</th>
                <th>สถานะ</th>
                <th>แจ้งเมื่อ</th>
                <th>จัดการ</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => {
                const catMeta = TICKET_CATEGORIES[t.category] || { label: t.category, cls: 'badge-muted' }
                const priMeta = TICKET_PRIORITIES[t.priority] || { label: t.priority, cls: 'badge-muted' }
                const statMeta = TICKET_STATUSES[t.status] || { label: t.status, cls: 'badge-muted' }
                const isActive = activeId === t.id
                return [
                  <tr key={t.id}>
                    <td>{t.id}</td>
                    <td>#{t.user_id}</td>
                    <td>{t.subject}</td>
                    <td><span className={`badge ${catMeta.cls}`}>{catMeta.label}</span></td>
                    <td><span className={`badge ${priMeta.cls}`}>{priMeta.label}</span></td>
                    <td>
                      <span className={`badge ${statMeta.cls}`}>{statMeta.label}</span>
                      <select
                        className="mini-select"
                        value={t.status}
                        onChange={(e) => handleUpdate(t.id, { status: e.target.value })}
                        title="เปลี่ยนสถานะ"
                      >
                        {Object.entries(TICKET_STATUSES).map(([v, m]) => (
                          <option key={v} value={v}>{m.label}</option>
                        ))}
                      </select>
                    </td>
                    <td className="muted small">{formatDateTime(t.created_at)}</td>
                    <td>
                      <button
                        className="btn btn-sm btn-ghost"
                        onClick={() => setActiveId(isActive ? null : t.id)}
                      >
                        {isActive ? 'ซ่อน' : 'รายละเอียด'}
                      </button>
                      <button className="btn btn-danger-sm" onClick={() => handleDelete(t.id)}>
                        ลบ
                      </button>
                    </td>
                  </tr>,
                  isActive && (
                    <tr className="detail-row" key={`${t.id}-detail`}>
                      <td colSpan={8}>
                        <TicketDetail
                          ticket={t}
                          onSave={handleUpdate}
                        />
                      </td>
                    </tr>
                  ),
                ]
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function TicketDetail({ ticket, onSave }) {
  const [notes, setNotes] = useState(ticket.resolution_notes || '')
  const [saving, setSaving] = useState(false)

  async function save() {
    setSaving(true)
    await onSave(ticket.id, { resolution_notes: notes })
    setSaving(false)
  }

  return (
    <div className="ticket-detail">
      <p><strong>รายละเอียด:</strong> {ticket.description}</p>
      {ticket.assigned_to != null && (
        <p><strong>เจ้าหน้าที่ที่รับผิดชอบ:</strong> #{ticket.assigned_to}</p>
      )}
      {ticket.resolved_at && (
        <p><strong>แก้ไขเสร็จเมื่อ:</strong> {formatDateTime(ticket.resolved_at)}</p>
      )}
      <div className="field">
        <label>บันทึกการแก้ไข (Resolution Notes)</label>
        <textarea
          rows={2}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="หมายเหตุเมื่อจัดการเคสแล้ว..."
        />
      </div>
      <div>
        <button className="btn btn-sm btn-primary" onClick={save} disabled={saving}>
          {saving ? 'กำลังบันทึก...' : 'บันทึกบันทึกการแก้ไข'}
        </button>
      </div>
    </div>
  )
}