import { useState, useEffect } from 'react'
import { favoritesApi } from '../api'

const emptyForm = { user_id: '', favorite_type: 'bike', favorite_id: '', nickname: '' }

export default function FavoritesManager() {
  const [records, setRecords] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [editing, setEditing] = useState(null)
  const [error, setError] = useState('')
  const [userFilter, setUserFilter] = useState('')

  useEffect(() => { load() }, [])

  async function load(userId) {
    try {
      const data = userId ? await favoritesApi.listByUser(userId) : await favoritesApi.list()
      setRecords(data)
    } catch (e) { setError(e.message) }
  }

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  async function handleSubmit(e) {
    e.preventDefault()
    try {
      if (editing) {
        await favoritesApi.update(editing, { nickname: form.nickname })
      } else {
        await favoritesApi.create(form)
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
      favorite_type: rec.favorite_type,
      favorite_id: rec.favorite_id,
      nickname: rec.nickname || '',
    })
  }

  async function handleDelete(id) {
    if (!confirm('ลบรายการโปรดนี้?')) return
    try {
      await favoritesApi.delete(id)
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

  function typeLabel(t) {
    return t === 'bike' ? 'จักรยาน' : 'สถานี'
  }

  return (
    <div className="manager">
      <h2>รายการโปรด (Favorite Bicycles & Stations)</h2>
      {error && <p className="error" onClick={() => setError('')}>{error}</p>}

      <form onSubmit={handleSearchUser} className="filter-form">
        <label>ค้นหาตามรหัสผู้ใช้ <input placeholder="พิมพ์รหัสผู้ใช้แล้วกดค้นหา" value={userFilter} onChange={e => setUserFilter(e.target.value)} /></label>
        <button type="submit">ค้นหา</button>
        {userFilter && <button type="button" onClick={() => { setUserFilter(''); load() }}>แสดงทั้งหมด</button>}
      </form>

      <form onSubmit={handleSubmit} className="form">
        {!editing && (
          <>
            <label>รหัสผู้ใช้ <input name="user_id" placeholder="เช่น USER-001" value={form.user_id} onChange={handleChange} required /></label>
            <label>ประเภท
            <select name="favorite_type" value={form.favorite_type} onChange={handleChange}>
              <option value="bike">จักรยาน</option>
              <option value="station">สถานี</option>
            </select>
            </label>
            <label>รหัส{form.favorite_type === 'bike' ? 'จักรยาน' : 'สถานี'} <input name="favorite_id" placeholder={form.favorite_type === 'bike' ? 'เช่น BIKE-001' : 'เช่น สถานีสยาม'} value={form.favorite_id} onChange={handleChange} required /></label>
          </>
        )}
        <label>ชื่อเล่น <input name="nickname" placeholder={editing ? 'เช่น สถานีหน้าหอ' : 'ตั้งชื่อเล่น (ไม่จำเป็น)'} value={form.nickname} onChange={handleChange} /></label>

        <div className="form-actions">
          <button type="submit">{editing ? 'อัปเดตชื่อเล่น' : 'เพิ่ม'}</button>
          {editing && <button type="button" onClick={handleCancel}>ยกเลิก</button>}
        </div>
      </form>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>ผู้ใช้</th><th>ประเภท</th><th>รหัส</th><th>ชื่อเล่น</th><th>วันที่เพิ่ม</th><th>จัดการ</th>
            </tr>
          </thead>
          <tbody>
            {records.map(f => (
              <tr key={f.id}>
                <td>{f.id}</td>
                <td>{f.user_id}</td>
                <td>{typeLabel(f.favorite_type)}</td>
                <td>{f.favorite_id}</td>
                <td>{f.nickname || '-'}</td>
                <td>{new Date(f.created_at).toLocaleDateString('th-TH')}</td>
                <td className="actions">
                  <button onClick={() => handleEdit(f)}>ตั้งชื่อเล่น</button>
                  <button className="danger" onClick={() => handleDelete(f.id)}>ลบ</button>
                </td>
              </tr>
            ))}
            {records.length === 0 && (
              <tr><td colSpan={7} style={{ textAlign: 'center' }}>ไม่มีรายการโปรด</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
