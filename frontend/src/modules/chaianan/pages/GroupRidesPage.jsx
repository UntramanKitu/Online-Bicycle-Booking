import { useEffect, useState } from 'react'
import { api, getApiError } from '../../../api'
import { GROUP_STATUSES } from '../../../constants'
import { formatDateTime, toIso, toLocalInputValue } from '../../../utils'
import { useCurrentUser } from '../../../context/currentUser'

const emptyForm = () => ({
  name: '',
  destination: '',
  meetup_time: '',
  meetup_location: '',
  max_members: 4,
})

const tabs = [
  { value: '', label: 'ทั้งหมด', tone: 'all' },
  { value: 'open', label: 'เปิดรับสมาชิก', tone: 'open' },
  { value: 'full', label: 'เต็ม', tone: 'full' },
  { value: 'cancelled', label: 'ยกเลิก', tone: 'cancelled' },
]

export default function GroupRidesPage() {
  const { userId, getUserName } = useCurrentUser()
  const [groups, setGroups] = useState([])
  const [joined, setJoined] = useState(new Set())
  const [totalCount, setTotalCount] = useState(0)
  // แยกสถานะโหลดครั้งแรกออกจากการกดสลับแท็บ
  // ถ้าใช้ loading เดียว การกดแท็บจะทำให้กริดทั้งหมดถูกแทนด้วย "กำลังโหลด..." ทั้งหน้า
  const [initialLoading, setInitialLoading] = useState(true)
  const [status, setStatus] = useState('')
  const [form, setForm] = useState(emptyForm())
  const [clearing, setClearing] = useState(false)
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

  async function load(isFirstLoad = false) {
    if (isFirstLoad) setInitialLoading(true)
    try {
      if (status) {
        const res = await api.get('/group-rides', { params: { status } })
        setGroups(res.data)
      } else {
        const res = await api.get('/group-rides')
        setGroups(res.data)
        // นับจำนวนทั้งหมดจากผลลัพธ์ที่ไม่ถูกกรอง เพื่อให้แท็บ "ทั้งหมด" แสดงตัวเลขที่ถูกต้องเสมอ
        setTotalCount(res.data.length)
      }
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      if (isFirstLoad) setInitialLoading(false)
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      load(true)
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

  async function handleClearCancelled() {
    if (!window.confirm('ลบกลุ่มปั่นที่ยกเลิกแล้วทั้งหมด?\n(กลุ่มที่ยังเปิดอยู่หรือเต็มแล้วจะไม่ถูกลบ)')) return
    setMessage(null)
    setClearing(true)
    try {
      const res = await api.delete('/group-rides/cancelled')
      setMessage({
        type: 'success',
        text: res.data.removed > 0
          ? `ลบกลุ่มที่ยกเลิกแล้ว ${res.data.removed} กลุ่ม`
          : 'ไม่มีกลุ่มที่ยกเลิกแล้วให้ลบ',
      })
      await load()
      await loadJoined()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setClearing(false)
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
            <label>หัวหน้ากลุ่ม</label>
            <input type="text" value={getUserName(userId)} disabled />
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

      <div className="tabs tabs-with-action">
        <div className="tabs-list">
          {tabs.map((t) => (
            <button
              key={t.value}
              className={`tab tab-tone-${t.tone} ${status === t.value ? 'active' : ''}`}
              onClick={() => setStatus(t.value)}
            >
              {t.label}
              {t.value === '' ? ` (${totalCount})` : ''}
            </button>
          ))}
        </div>
        <button
          className="btn btn-sm btn-ghost"
          onClick={handleClearCancelled}
          disabled={clearing}
          title="ลบกลุ่มที่ยกเลิกแล้วออกทั้งหมด"
        >
          {clearing ? 'กำลังล้าง...' : 'ล้างกลุ่มที่ยกเลิก'}
        </button>
      </div>

      {initialLoading ? (
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
            const fillRatio = g.max_members ? Math.min(100, Math.round((g.current_members / g.max_members) * 100)) : 0
            return (
              <div className={`group-card status-${g.status}`} key={g.id}>
                {g.status === 'cancelled' && (
                  <div className="cancelled-banner">
                    <span className="cancelled-banner-text">ยกเลิกแล้ว</span>
                  </div>
                )}
                <div className="group-card-head">
                  <h3>{g.name}</h3>
                  <span className={`badge ${meta.cls}`}>{meta.label}</span>
                </div>
                <div className="group-meta group-meta-block">
                  <span><em>หัวหน้ากลุ่ม</em> <strong>{getUserName(g.created_by)}</strong></span>
                  <span><em>จุดหมาย</em> <strong>{g.destination}</strong></span>
                  <span><em>เวลานัด</em> <strong>{formatDateTime(g.meetup_time)}</strong></span>
                  <span><em>สถานที่นัดพบ</em> <strong>{g.meetup_location || '-'}</strong></span>
                </div>
                <div className="member-progress">
                  <div className="member-progress-head">
                    <span>สมาชิก</span>
                    <strong className="member-count">{g.current_members}/{g.max_members}</strong>
                  </div>
                  <div className="member-progress-track">
                    <div
                      className={`member-progress-fill ${fillRatio >= 100 ? 'is-full' : ''}`}
                      style={{ width: `${fillRatio}%` }}
                    />
                  </div>
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
                        <span>{getUserName(m.user_id)}</span>
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