import { useState, useEffect } from 'react'
import { penaltiesApi, returnsApi } from '../api'

const emptyForm = { user_id: '', return_id: '', points: 1, reason: '' }

export default function PenaltiesManager() {
  const [records, setRecords] = useState([])
  const [returns, setReturns] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [editing, setEditing] = useState(null)
  const [error, setError] = useState('')
  const [userFilter, setUserFilter] = useState('')

  useEffect(() => { load(); loadReturns() }, [])

  async function load(userId) {
    try {
      const data = userId ? await penaltiesApi.getUserPenalties(userId) : await penaltiesApi.list()
      setRecords(data)
    } catch (e) { setError(e.message) }
  }

  async function loadReturns() {
    try { setReturns(await returnsApi.list()) } catch (_) {}
  }

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    try {
      const payload = { ...form, return_id: form.return_id ? Number(form.return_id) : null, points: Number(form.points) }
      if (editing) {
        await penaltiesApi.update(editing, payload)
      } else {
        await penaltiesApi.create(payload)
      }
      setForm(emptyForm)
      setEditing(null)
      await load(userFilter)
    } catch (e) { setError(e.message) }
  }

  async function handleEdit(rec) {
    setEditing(rec.id)
    setForm({
      user_id: rec.user_id,
      return_id: rec.return_id || '',
      points: rec.points,
      reason: rec.reason,
    })
  }

  async function handleDelete(id) {
    if (!confirm('ลบบทลงโทษนี้?')) return
    try {
      await penaltiesApi.delete(id)
      await load(userFilter)
    } catch (e) { setError(e.message) }
  }

  function handleCancel() {
    setForm(emptyForm)
    setEditing(null)
  }

  function handleSearchUser(e) {
    e.preventDefault()
    load(userFilter)
  }

  return (
    <div className="manager">
      <h2>จัดการบทลงโทษ (Penalty Strikes)</h2>
      {error && <p className="error" onClick={() => setError('')}>{error}</p>}

      <form onSubmit={handleSearchUser} className="filter-form">
        <label>ค้นหาตามรหัสผู้ใช้ <input placeholder="พิมพ์รหัสผู้ใช้แล้วกดค้นหา" value={userFilter} onChange={e => setUserFilter(e.target.value)} /></label>
        <button type="submit">ค้นหา</button>
        {userFilter && <button type="button" onClick={() => { setUserFilter(''); load() }}>แสดงทั้งหมด</button>}
      </form>

      <form onSubmit={handleSubmit} className="form">
        <label>รหัสผู้ใช้ <input name="user_id" placeholder="เช่น USER-001" value={form.user_id} onChange={handleChange} required /></label>
        <label>บันทึกการคืน (ไม่จำเป็น)
        <select name="return_id" value={form.return_id} onChange={handleChange}>
          <option value="">-- ไม่ระบุ --</option>
          {returns.map(r => (
            <option key={r.id} value={r.id}>#{r.id} - {r.bike_id}</option>
          ))}
        </select>
        </label>
        <label>แต้มโทษ <input name="points" type="number" min={1} placeholder="จำนวนแต้ม" value={form.points} onChange={handleChange} required /></label>
        <label>เหตุผล <textarea name="reason" placeholder="ระบุสาเหตุของการลงโทษ" value={form.reason} onChange={handleChange} required rows={2} /></label>

        {editing && (
          <label>สถานะ
          <select name="status" value={form.status || 'active'} onChange={handleChange}>
            <option value="active"> active</option>
            <option value="appealed">อุทธรณ์</option>
            <option value="removed">ยกเลิก</option>
          </select>
          </label>
        )}

        <div className="form-actions">
          <button type="submit">{editing ? 'อัปเดต' : 'เพิ่ม'}</button>
          {editing && <button type="button" onClick={handleCancel}>ยกเลิก</button>}
        </div>
      </form>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>ผู้ใช้</th><th>บันทึกการคืน</th><th>คะแนน</th><th>เหตุผล</th><th>สถานะ</th><th>วันที่</th><th>จัดการ</th>
            </tr>
          </thead>
          <tbody>
            {records.map(p => (
              <tr key={p.id}>
                <td>{p.id}</td>
                <td>{p.user_id}</td>
                <td>{p.return_id ? `#${p.return_id}` : '-'}</td>
                <td>{p.points}</td>
                <td>{p.reason}</td>
                <td>{penaltyStatusLabel(p.status)}</td>
                <td>{new Date(p.created_at).toLocaleDateString('th-TH')}</td>
                <td className="actions">
                  <button onClick={() => handleEdit(p)}>แก้ไข</button>
                  <button className="danger" onClick={() => handleDelete(p.id)}>ลบ</button>
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

function penaltyStatusLabel(s) {
  const map = { active: 'active', appealed: 'อุทธรณ์', removed: 'ยกเลิก' }
  return map[s] || s
}
