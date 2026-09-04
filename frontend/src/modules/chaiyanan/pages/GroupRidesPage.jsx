import { useEffect, useState } from 'react'
import { api, getApiError } from '../../../api'
import { GROUP_STATUSES } from '../../../constants'
import { formatDateTime, toIso, toLocalInputValue } from '../../../utils'
import { useCurrentUser } from '../../../context/CurrentUserContext'

const emptyForm = () => ({
  name: '',
  destination: '',
  meetup_time: '',
  meetup_location: '',
  max_members: 4,
})

const tabs = [
  { value: '', label: 'ทั้งหมด' },
  { value: 'open', label: 'เปิดรับสมาชิก' },
  { value: 'full', label: 'เต็ม' },
  { value: 'cancelled', label: 'ยกเลิก' },
]

export default function GroupRidesPage() {
  const { userId } = useCurrentUser()
  const [groups, setGroups] = useState([])
  const [joined, setJoined] = useState(new Set())
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState('')
  const [form, setForm] = useState(emptyForm())
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [membership, setMembership] = useState({})
  const [expanded, setExpanded] = useState({})
  const [editingId, setEditingId] = useState(null)

  async function loadJoined() {
    try {
      const res = await api.get('/group-rides', { params: { user_id: userId } })
      setJoined(new Set(res.data.map((g) => g.id)))
    } catch {
      setJoined(new Set())
    }
  }

  async function load() {
    setLoading(true)
    try {
      const params = status ? { status } : {}
      const res = await api.get('/group-rides', { params })
      setGroups(res.data)
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      load()
      loadJoined()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [status, userId]) // eslint-disable-line react-hooks/exhaustive-deps

  async function toggleMembers(id) {
    const next = { ...expanded, [id]: !expanded[id] }
    setExpanded(next)
    if (next[id] && !membership[id]) {
      try {
        const res = await api.get(`/group-rides/${id}`)
        setMembership((m) => ({ ...m, [id]: res.data.members || [] }))
      } catch (err) {
        setMessage({ type: 'error', text: getApiError(err) })
      }
    }
  }

  function updateField(key, value) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  async function handleCreate(e) {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    try {
      await api.post('/group-rides', {
        created_by: userId,
        name: form.name,
        destination: form.destination,
        meetup_time: toIso(form.meetup_time),
        meetup_location: form.meetup_location || null,
        max_members: Number(form.max_members),
      })
      setMessage({ type: 'success', text: 'สร้างกลุ่มปั่นเรียบร้อย ✓' })
      setForm(emptyForm())
      setShowForm(false)
      load()
      loadJoined()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setSaving(false)
    }
  }

  async function runAction(actionFn) {
    setMessage(null)
    try {
      await actionFn()
      load()
      loadJoined()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    }
  }

  const handleJoin = (id) => runAction(() => api.post(`/group-rides/${id}/join`, { user_id: userId }))
  const handleLeave = (id) => runAction(() => api.post(`/group-rides/${id}/leave`, { user_id: userId }))
  const handleCancel = (id) => {
    if (!window.confirm('ยืนยันการยกเลิกกลุ่มนี้หรือไม่?')) return
    runAction(() => api.delete(`/group-rides/${id}`, { params: { user_id: userId } }))
  }
  const handleSaveEdit = (id, data) =>
    runAction(() => api.put(`/group-rides/${id}`, data, { params: { user_id: userId } }))

  return (
    <div className="page-section">
      <div className="section-head">
        <div>
          <h1 className="section-title">Group Ride Bookings</h1>
          <p className="section-subtitle">
            ระบบตารางกลุ่มปั่นร่วมกัน · หาเพื่อนร่วมทางและเพิ่มความปลอดภัยในการเดินทางเป็นกลุ่ม
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? 'ปิดฟอร์ม' : '+ สร้างกลุ่มปั่น'}
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
            <label>หัวหน้ากลุ่ม (user_id)</label>
            <input type="number" value={userId} disabled />
          </div>
          <div className="field">
            <label>ชื่อกลุ่ม *</label>
            <input
              required
              placeholder="เช่น ปั่นเที่ยวหอสมุด หลังเลิกเรียน"
              value={form.name}
              onChange={(e) => updateField('name', e.target.value)}
            />
          </div>
          <div className="field">
            <label>จุดหมายปลายทาง *</label>
            <input
              required
              placeholder="เช่น หอสมุดกลาง"
              value={form.destination}
              onChange={(e) => updateField('destination', e.target.value)}
            />
          </div>
          <div className="field">
            <label>เวลานัดหมาย *</label>
            <input
              type="datetime-local"
              required
              value={form.meetup_time}
              onChange={(e) => updateField('meetup_time', e.target.value)}
            />
          </div>
          <div className="field">
            <label>สถานที่นัดพบ</label>
            <input
              placeholder="เช่น ประตูคณะวิทยาศาสตร์"
              value={form.meetup_location}
              onChange={(e) => updateField('meetup_location', e.target.value)}
            />
          </div>
          <div className="field">
            <label>จำนวนสมาชิกที่เปิดรับ *</label>
            <input
              type="number"
              min="2"
              max="50"
              required
              value={form.max_members}
              onChange={(e) => updateField('max_members', e.target.value)}
            />
          </div>
          <div className="form-actions">
            <button className="btn btn-primary" disabled={saving}>
              {saving ? 'กำลังสร้าง...' : 'สร้างกลุ่ม'}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>
              ยกเลิก
            </button>
          </div>
        </form>
      )}

      <div className="tabs">
        {tabs.map((t) => (
          <button
            key={t.value}
            className={status === t.value ? 'tab active' : 'tab'}
            onClick={() => setStatus(t.value)}
          >
            {t.label}
            {t.value === '' ? ` (${groups.length})` : ''}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="empty">กำลังโหลดข้อมูล...</p>
      ) : groups.length === 0 ? (
        <p className="empty">ยังไม่มีกลุ่มปั่นในรายการนี้</p>
      ) : (
        <div className="grid-cards">
          {groups.map((g) => {
            const meta = GROUP_STATUSES[g.status] || { label: g.status, cls: 'badge-muted' }
            const isLeader = g.created_by === userId
            const isJoined = joined.has(g.id)
            const isExpanded = expanded[g.id]
            const isEditing = editingId === g.id
            return (
              <div className="group-card" key={g.id}>
                <div className="group-card-head">
                  <h3>{g.name}</h3>
                  <span className={`badge ${meta.cls}`}>{meta.label}</span>
                </div>
                <div className="group-meta">
                  <span>หัวหน้า <strong>#{g.created_by}</strong></span>
                  <span>จุดหมาย <strong>{g.destination}</strong></span>
                  <span>เวลา <strong>{formatDateTime(g.meetup_time)}</strong></span>
                </div>
                <div className="group-meta">
                  <span>นัดพบ <strong>{g.meetup_location || '-'}</strong></span>
                  <span>
                    สมาชิก <strong className="member-count">{g.current_members}/{g.max_members}</strong>
                  </span>
                </div>
                <div className="group-actions">
                  {isEditing && (
                    <GroupEditForm
                      group={g}
                      onSave={handleSaveEdit}
                      onClose={() => setEditingId(null)}
                    />
                  )}
                  {isLeader && !isEditing && (
                    <button
                      className="btn btn-sm btn-ghost"
                      onClick={() => setEditingId(g.id)}
                    >
                      แก้ไข
                    </button>
                  )}
                  {isLeader && g.status !== 'cancelled' && g.status !== 'completed' && (
                    <button className="btn btn-danger-sm" onClick={() => handleCancel(g.id)}>
                      ยกเลิกกลุ่ม
                    </button>
                  )}
                  {!isLeader && isJoined && g.status !== 'cancelled' && g.status !== 'completed' && (
                    <button className="btn btn-sm btn-ghost" onClick={() => handleLeave(g.id)}>
                      ออกจากกลุ่ม
                    </button>
                  )}
                  {!isLeader && !isJoined && g.status === 'open' && (
                    <button className="btn btn-sm btn-primary" onClick={() => handleJoin(g.id)}>
                      เข้าร่วม
                    </button>
                  )}
                  {!isLeader && !isJoined && g.status === 'full' && (
                    <span className="muted small">เต็มแล้ว</span>
                  )}
                  <button className="btn btn-sm btn-ghost" onClick={() => toggleMembers(g.id)}>
                    {isExpanded ? 'ซ่อนสมาชิก' : 'สมาชิก'}
                  </button>
                </div>
                {isExpanded && (
                  <div className="members-list">
                    {(membership[g.id] || []).map((m) => (
                      <div className="member-row" key={m.id}>
                        <span>สมาชิก #{m.user_id}</span>
                        <span className={`role-tag ${m.role === 'leader' ? 'role-leader' : 'role-member'}`}>
                          {m.role === 'leader' ? 'หัวหน้ากลุ่ม' : 'สมาชิก'}
                        </span>
                      </div>
                    ))}
                    {(membership[g.id] || []).length === 0 && (
                      <span className="muted small">กำลังโหลดสมาชิก...</span>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function GroupEditForm({ group, onSave, onClose }) {
  const [form, setForm] = useState({
    name: group.name,
    destination: group.destination,
    meetup_time: toLocalInputValue(group.meetup_time),
    meetup_location: group.meetup_location || '',
    max_members: group.max_members,
  })
  const [saving, setSaving] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setSaving(true)
    await onSave(group.id, {
      name: form.name,
      destination: form.destination,
      meetup_time: toIso(form.meetup_time),
      meetup_location: form.meetup_location || null,
      max_members: Number(form.max_members),
    })
    setSaving(false)
    onClose()
  }

  return (
    <form className="form-grid edit-form" onSubmit={submit}>
      <div className="field">
        <label>ชื่อกลุ่ม</label>
        <input
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
      </div>
      <div className="field">
        <label>จุดหมาย</label>
        <input
          value={form.destination}
          onChange={(e) => setForm({ ...form, destination: e.target.value })}
          required
        />
      </div>
      <div className="field">
        <label>เวลานัดหมาย</label>
        <input
          type="datetime-local"
          value={form.meetup_time}
          onChange={(e) => setForm({ ...form, meetup_time: e.target.value })}
          required
        />
      </div>
      <div className="field">
        <label>สถานที่นัดพบ</label>
        <input
          value={form.meetup_location}
          onChange={(e) => setForm({ ...form, meetup_location: e.target.value })}
        />
      </div>
      <div className="field">
        <label>เปิดรับสมาชิก</label>
        <input
          type="number"
          min="2"
          max="50"
          value={form.max_members}
          onChange={(e) => setForm({ ...form, max_members: e.target.value })}
          required
        />
      </div>
      <div className="form-actions">
        <button className="btn btn-sm btn-primary" disabled={saving}>
          {saving ? 'บันทึก...' : 'บันทึกแก้ไข'}
        </button>
        <button type="button" className="btn btn-sm btn-ghost" onClick={onClose}>
          ปิด
        </button>
      </div>
    </form>
  )
}