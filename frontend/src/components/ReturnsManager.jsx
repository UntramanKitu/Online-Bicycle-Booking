import { useState, useEffect } from 'react'
import { returnsApi } from '../api'

const emptyForm = { bike_id: '', user_id: '', return_time: '', station: '', status: 'on_time', notes: '' }

export default function ReturnsManager() {
  const [records, setRecords] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [editing, setEditing] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => { load() }, [])

  async function load() {
    try { setRecords(await returnsApi.list()) } catch (e) { setError(e.message) }
  }

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    try {
      if (editing) {
        const payload = { ...form }
        if (payload.return_time) payload.return_time = new Date(payload.return_time).toISOString()
        await returnsApi.update(editing, payload)
      } else {
        await returnsApi.create({ ...form, return_time: new Date(form.return_time).toISOString() })
      }
      setForm(emptyForm)
      setEditing(null)
      await load()
    } catch (e) { setError(e.message) }
  }

  async function handleEdit(rec) {
    setEditing(rec.id)
    setForm({
      bike_id: rec.bike_id,
      user_id: rec.user_id,
      return_time: rec.return_time.slice(0, 16),
      station: rec.station,
      status: rec.status,
      notes: rec.notes || '',
    })
  }

  async function handleDelete(id) {
    if (!confirm('ลบบันทึกนี้?')) return
    try {
      await returnsApi.delete(id)
      await load()
    } catch (e) { setError(e.message) }
  }

  function handleCancel() {
    setForm(emptyForm)
    setEditing(null)
  }

  return (
    <div className="manager">
      <h2>จัดการบันทึกการคืนจักรยาน</h2>
      {error && <p className="error" onClick={() => setError('')}>{error}</p>}

      <form onSubmit={handleSubmit} className="form">
        <label>รหัสจักรยาน <input name="bike_id" placeholder="เช่น BIKE-001" value={form.bike_id} onChange={handleChange} required /></label>
        <label>รหัสผู้ใช้ <input name="user_id" placeholder="เช่น USER-001" value={form.user_id} onChange={handleChange} required /></label>
        <label>เวลาคืน <input name="return_time" type="datetime-local" value={form.return_time} onChange={handleChange} required /></label>
        <label>สถานีคืน
        <select name="station" value={form.station} onChange={handleChange} required>
          <option value="">-- เลือกสถานี --</option>
          <option value="สถานีศูนย์กีฬากลาง">สถานีศูนย์กีฬากลาง</option>
          <option value="รอเพิ่มเติม">รอเพิ่มเติม</option>
          
        </select>
        </label>
        <label>สถานะ
        <select name="status" value={form.status} onChange={handleChange}>
          <option value="on_time">ตรงเวลา</option>
          <option value="late">สาย</option>
          <option value="damaged">เสียหาย</option>
        </select>
        </label>
        <label>หมายเหตุ <textarea name="notes" placeholder="บันทึกเพิ่มเติม (ถ้ามี)" value={form.notes} onChange={handleChange} rows={2} /></label>
        <div className="form-actions">
          <button type="submit">{editing ? 'อัปเดต' : 'เพิ่ม'}</button>
          {editing && <button type="button" onClick={handleCancel}>ยกเลิก</button>}
        </div>
      </form>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>รหัสจักรยาน</th><th>ผู้ใช้</th><th>เวลาคืน</th>
              <th>สถานี</th><th>สถานะ</th><th>หมายเหตุ</th><th>จัดการ</th>
            </tr>
          </thead>
          <tbody>
            {records.map(r => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{r.bike_id}</td>
                <td>{r.user_id}</td>
                <td>{new Date(r.return_time).toLocaleString('th-TH')}</td>
                <td>{r.station}</td>
                <td>{statusLabel(r.status)}</td>
                <td>{r.notes || '-'}</td>
                <td className="actions">
                  <button onClick={() => handleEdit(r)}>แก้ไข</button>
                  <button className="danger" onClick={() => handleDelete(r.id)}>ลบ</button>
                </td>
              </tr>
            ))}
            {records.length === 0 && (
              <tr><td colSpan={8} style={{ textAlign: 'center' }}>ไม่มีข้อมูล</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function statusLabel(s) {
  const map = { on_time: 'ตรงเวลา', late: 'สาย', damaged: 'เสียหาย' }
  return map[s] || s
}
