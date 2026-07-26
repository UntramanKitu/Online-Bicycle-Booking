import { useState, useEffect } from 'react'
import { damagesApi, returnsApi } from '../api'

const emptyForm = { return_id: '', description: '', severity: 'minor', images: null }

export default function DamagesManager() {
  const [records, setRecords] = useState([])
  const [returns, setReturns] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [editing, setEditing] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => { load(); loadReturns() }, [])

  async function load() {
    try { setRecords(await damagesApi.list()) } catch (e) { setError(e.message) }
  }

  async function loadReturns() {
    try { setReturns(await returnsApi.list()) } catch (_) {}
  }

  function handleChange(e) {
    const { name, value, files } = e.target
    if (name === 'images') {
      setForm({ ...form, images: files })
    } else {
      setForm({ ...form, [name]: value })
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    try {
      const fd = new FormData()
      fd.append('return_id', form.return_id)
      fd.append('description', form.description)
      fd.append('severity', form.severity)
      if (form.images) {
        Array.from(form.images).forEach(f => fd.append('images', f))
      }

      if (editing) {
        await damagesApi.update(editing, fd)
      } else {
        await damagesApi.create(fd)
      }
      setForm(emptyForm)
      setEditing(null)
      await load()
    } catch (e) { setError(e.message) }
  }

  async function handleEdit(rec) {
    setEditing(rec.id)
    setForm({
      return_id: rec.return_id,
      description: rec.description,
      severity: rec.severity,
      images: null,
    })
  }

  async function handleDelete(id) {
    if (!confirm('ลบบันทึกความเสียหายนี้?')) return
    try {
      await damagesApi.delete(id)
      await load()
    } catch (e) { setError(e.message) }
  }

  function handleCancel() {
    setForm(emptyForm)
    setEditing(null)
  }

  return (
    <div className="manager">
      <h2>จัดการหลักฐานความเสียหาย</h2>
      {error && <p className="error" onClick={() => setError('')}>{error}</p>}

      <form onSubmit={handleSubmit} className="form">
        <label>บันทึกการคืน
        <select name="return_id" value={form.return_id} onChange={handleChange} required>
          <option value="">-- เลือกบันทึกการคืน --</option>
          {returns.map(r => (
            <option key={r.id} value={r.id}>
              #{r.id} - {r.bike_id} ({r.user_id})
            </option>
          ))}
        </select>
        </label>
        <label>รายละเอียด <textarea name="description" placeholder="อธิบายความเสียหายที่พบ" value={form.description} onChange={handleChange} required rows={3} /></label>
        <label>ระดับความรุนแรง
        <select name="severity" value={form.severity} onChange={handleChange}>
          <option value="minor">เล็กน้อย</option>
          <option value="moderate">ปานกลาง</option>
          <option value="severe">รุนแรง</option>
        </select>
        </label>
        <label>รูปภาพความเสียหาย <input name="images" type="file" multiple accept="image/*" onChange={handleChange} /></label>
        <div className="form-actions">
          <button type="submit">{editing ? 'อัปเดต' : 'เพิ่ม'}</button>
          {editing && <button type="button" onClick={handleCancel}>ยกเลิก</button>}
        </div>
      </form>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>บันทึกการคืน</th><th>รายละเอียด</th><th>ระดับ</th><th>รูปภาพ</th><th>วันที่</th><th>จัดการ</th>
            </tr>
          </thead>
          <tbody>
            {records.map(d => (
              <tr key={d.id}>
                <td>{d.id}</td>
                <td>#{d.return_id}</td>
                <td>{d.description}</td>
                <td>{severityLabel(d.severity)}</td>
                <td>
                  {d.image_paths ? d.image_paths.split(',').map(fn => (
                    <img key={fn} src={`/uploads/${fn}`} alt="" className="thumb" />
                  )) : '-'}
                </td>
                <td>{new Date(d.created_at).toLocaleDateString('th-TH')}</td>
                <td className="actions">
                  <button onClick={() => handleEdit(d)}>แก้ไข</button>
                  <button className="danger" onClick={() => handleDelete(d.id)}>ลบ</button>
                </td>
              </tr>
            ))}
            {records.length === 0 && (
              <tr><td colSpan={7} style={{ textAlign: 'center' }}>ไม่มีข้อมูล</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function severityLabel(s) {
  const map = { none: 'ไม่มีความเสียหาย', minor: 'เล็กน้อย', moderate: 'ปานกลาง', severe: 'รุนแรง' }
  return map[s] || s
}
