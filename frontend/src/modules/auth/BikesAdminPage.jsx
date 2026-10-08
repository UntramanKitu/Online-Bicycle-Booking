import { useEffect, useState } from 'react'
import { api, getApiError } from '../../api'
import { useCurrentUser } from '../../context/currentUser'

const emptyForm = () => ({ code: '', type: 'ธรรมดา', model: '', station: '', distance: '', battery: '' })

const TYPE_OPTIONS = ['ธรรมดา', 'ไฟฟ้า', 'พับได้', 'เสือภูเขา']

/** prefix รหัสออโต้ตามประเภท (ตรงกับ backend: E/N/P/T-BIKE-xxx) */
const TYPE_CODE_PREFIX = { ธรรมดา: 'N', ไฟฟ้า: 'E', พับได้: 'P', เสือภูเขา: 'T' }

/** หน้าแอดมิน: เพิ่ม / แก้ไข / เปิด-ปิดใช้ / ลบ จักรยาน (M02) */
export default function BikesAdminPage() {
  const { currentUser, usersLoading } = useCurrentUser()
  const [bikes, setBikes] = useState([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null) // กำลังแก้ไขคันไหน (null = เพิ่มใหม่)
  const [form, setForm] = useState(emptyForm())
  const [saving, setSaving] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const res = await api.get('/bicycles')
      setBikes(res.data)
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // เลื่อนไป task ถัดไป — กันกฎ react-hooks/set-state-in-effect (setState ใน effect)
    const timer = window.setTimeout(() => load(), 0)
    return () => window.clearTimeout(timer)
  }, [])

  function startCreate() {
    setEditingId(null)
    setForm(emptyForm())
    setShowForm(true)
    setMessage(null)
  }

  function startEdit(bike) {
    setEditingId(bike.id)
    setForm({
      code: bike.code || '',
      type: bike.type || 'ธรรมดา',
      model: bike.model || '',
      station: bike.station || '',
      distance: bike.distance || '',
      battery: bike.battery == null ? '' : String(bike.battery),
    })
    setShowForm(true)
    setMessage(null)
  }

  function closeForm() {
    setShowForm(false)
    setEditingId(null)
    setForm(emptyForm())
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    const payload = {
      type: form.type,
      model: form.model.trim(),
      station: form.station.trim(),
      distance: form.distance.trim() || '-',
      // แบตเตอรี่มีเฉพาะจักรยานไฟฟ้า — ประเภทอื่นส่ง null
      battery: form.type === 'ไฟฟ้า' && form.battery !== '' ? Number(form.battery) : null,
    }
    if (editingId) payload.code = form.code.trim() || null // เพิ่มใหม่ไม่ส่ง code — backend สร้างให้ตามประเภท
    try {
      if (editingId) {
        await api.put(`/bicycles/${editingId}`, payload)
        setMessage({ type: 'success', text: 'แก้ไขข้อมูลจักรยานเรียบร้อย ✓' })
      } else {
        await api.post('/bicycles', payload)
        setMessage({ type: 'success', text: 'เพิ่มจักรยานใหม่เรียบร้อย ✓' })
      }
      closeForm()
      await load()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setSaving(false)
    }
  }

  async function toggleStatus(bike) {
    setMessage(null)
    try {
      await api.patch(`/bicycles/${bike.id}/status`, { is_active: !bike.is_active })
      setMessage({
        type: 'success',
        text: bike.is_active ? `ปิดใช้ ${bike.code} แล้ว (จะจองไม่ได้)` : `เปิดใช้ ${bike.code} แล้ว`,
      })
      await load()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    }
  }

  async function handleDelete(bike) {
    if (!window.confirm(`ต้องการลบ ${bike.code} (${bike.model}) ออกจากระบบ?\nถ้ามีข้อมูลอ้างอิง (การจอง/รีวิว) จะลบไม่ได้ — ให้ใช้ "ปิดใช้" แทน`)) return
    setMessage(null)
    try {
      await api.delete(`/bicycles/${bike.id}`)
      setMessage({ type: 'success', text: `ลบ ${bike.code} เรียบร้อย` })
      await load()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    }
  }

  if (!usersLoading && !currentUser) {
    return <p className="empty">กรุณาเข้าสู่ระบบด้วย Google ก่อนใช้งาน</p>
  }

  const activeCount = bikes.filter((b) => b.is_active).length
  const busyCount = bikes.filter((b) => !b.available).length

  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <div>
          <h1 className="admin-title">
            <span className="admin-title-icon">🚲</span>
            จัดการจักรยาน (M02)
          </h1>
          <p className="admin-subtitle">เพิ่ม / แก้ไข / เปิด-ปิดใช้ / ลบ จักรยานในระบบ</p>
        </div>
        <div className="section-head-actions">
          <button className="btn btn-ghost" onClick={load} disabled={loading}>
            {loading ? '⏳' : '🔄'} รีเฟรช
          </button>
          <button className="btn btn-primary" onClick={showForm ? closeForm : startCreate}>
            {showForm ? 'ปิดฟอร์ม' : '+ เพิ่มจักรยาน'}
          </button>
        </div>
      </div>

      <div className="admin-stats">
        <div className="admin-stat-card">
          <span className="admin-stat-number">{bikes.length}</span>
          <span className="admin-stat-label">จักรยานทั้งหมด</span>
        </div>
        <div className="admin-stat-card admin-stat-card-user">
          <span className="admin-stat-number">{activeCount}</span>
          <span className="admin-stat-label">เปิดใช้งาน</span>
        </div>
        <div className="admin-stat-card admin-stat-card-admin">
          <span className="admin-stat-number">{busyCount}</span>
          <span className="admin-stat-label">กำลังถูกใช้งาน/จอง</span>
        </div>
      </div>

      {message && (
        <div className={`alert ${message.type === 'error' ? 'alert-error' : 'alert-success'}`}>
          {message.text}
          <button className="alert-close" onClick={() => setMessage(null)}>×</button>
        </div>
      )}

      {showForm && (
        <form className="panel form-grid" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="bike-code">รหัสจักรยาน</label>
            {editingId ? (
              <input
                id="bike-code"
                maxLength={20}
                placeholder="เช่น N-BIKE-001"
                value={form.code}
                onChange={(e) => setForm({ ...form, code: e.target.value })}
              />
            ) : (
              <>
                <input
                  id="bike-code"
                  value={`${TYPE_CODE_PREFIX[form.type] || 'N'}-BIKE-xxx`}
                  readOnly
                  aria-describedby="bike-code-hint"
                />
                <p id="bike-code-hint" className="muted small">
                  ระบบสร้างรหัสให้อัตโนมัติตามประเภท (prefix {TYPE_CODE_PREFIX[form.type] || 'N'}) — ไม่ต้องกรอก
                </p>
              </>
            )}
          </div>
          <div className="field">
            <label htmlFor="bike-type">ประเภท *</label>
            <select id="bike-type" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
              {TYPE_OPTIONS.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="bike-model">รุ่น/ชื่อ *</label>
            <input
              id="bike-model"
              required
              maxLength={100}
              placeholder="เช่น เสือหมอบ, ไฟฟ้า E-Bike"
              value={form.model}
              onChange={(e) => setForm({ ...form, model: e.target.value })}
            />
          </div>
          <div className="field">
            <label htmlFor="bike-station">สถานีจอด *</label>
            <input
              id="bike-station"
              required
              maxLength={100}
              placeholder="เช่น สถานีคณะวิศวะ"
              value={form.station}
              onChange={(e) => setForm({ ...form, station: e.target.value })}
            />
          </div>
          <div className="field">
            <label htmlFor="bike-distance">ระยะทางจากคุณ</label>
            <input
              id="bike-distance"
              maxLength={20}
              placeholder="เช่น 120 ม. (ใช้เรียงตามระยะใกล้สุด)"
              value={form.distance}
              onChange={(e) => setForm({ ...form, distance: e.target.value })}
            />
          </div>
          {form.type === 'ไฟฟ้า' && (
            <div className="field">
              <label htmlFor="bike-battery">แบตเตอรี่ (%)</label>
              <input
                id="bike-battery"
                type="number"
                min={0}
                max={100}
                placeholder="เช่น 80"
                value={form.battery}
                onChange={(e) => setForm({ ...form, battery: e.target.value })}
              />
            </div>
          )}
          <div className="form-actions">
            <button className="btn btn-primary" disabled={saving}>
              {saving ? 'กำลังบันทึก...' : editingId ? 'บันทึกการแก้ไข' : 'เพิ่มจักรยาน'}
            </button>
            <button type="button" className="btn btn-ghost" onClick={closeForm}>ยกเลิก</button>
          </div>
        </form>
      )}
      {loading ? (
        <div className="admin-loading"><div className="admin-spinner" /><p>กำลังโหลดข้อมูลจักรยาน...</p></div>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>#</th>
                <th>รหัส</th>
                <th>รุ่น / ประเภท</th>
                <th>สถานี</th>
                <th>ระยะทาง</th>
                <th>แบต</th>
                <th>สถานะ</th>
                <th>จัดการ</th>
              </tr>
            </thead>
            <tbody>
              {bikes.map((b) => (
                <tr key={b.id} className={b.is_active ? '' : 'admin-row-inactive'}>
                  <td className="admin-td-id">{b.id}</td>
                  <td><strong>{b.code}</strong></td>
                  <td>{b.model} <span className="muted small">({b.type})</span></td>
                  <td>{b.station}</td>
                  <td>{b.distance}</td>
                  <td>{b.battery != null ? `${b.battery}%` : '-'}</td>
                  <td>
                    <span className={`status-pill ${b.is_active ? (b.available ? 'free' : 'busy') : 'busy'}`}>
                      {!b.is_active ? 'ปิดใช้' : b.available ? 'ว่าง' : 'มีคนใช้'}
                    </span>
                  </td>
                  <td>
                    <div className="booking-actions">
                      <button className="btn btn-ghost btn-sm" onClick={() => startEdit(b)}>แก้ไข</button>
                      <button
                        className={`btn btn-sm ${b.is_active ? 'btn-danger-sm' : 'btn-primary'}`}
                        onClick={() => toggleStatus(b)}
                      >
                        {b.is_active ? 'ปิดใช้' : 'เปิดใช้'}
                      </button>
                      <button className="btn btn-ghost btn-sm" onClick={() => handleDelete(b)}>ลบ</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="admin-table-foot">แสดง {bikes.length} คัน</p>
        </div>
      )}
    </div>
  )
}
