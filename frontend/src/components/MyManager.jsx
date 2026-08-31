import { useState, useEffect } from 'react'
import { favoritesApi, penaltiesApi, lostItemsApi, pointsApi } from '../api'

const emptyFav = { user_id: '', target_type: 'bicycle', bicycle_id: '', station_name: '', nickname: '' }
const emptyPen = { user_id: '', reason: 'late_return', penalty_points: '1', action: 'warning', suspension_days: '', description: '', completed: false }
const emptyLost = { user_id: '', bicycle_id: '', item_name: '', location: '', image_url: '', description: '', status: 'lost' }
const emptyPoints = { user_id: '', points: '1', reason: 'good_return', description: '' }

const REASON_MAP = { late_return: 'คืนช้า', damaged: 'เสียหาย', lost: 'สูญหาย', other: 'อื่นๆ' }
const ACTION_MAP = { warning: 'เตือน', service: 'จิตอาสา', suspend: 'งดยืม' }
const LOST_STATUS_MAP = { lost: 'สูญหาย', found: 'พบแล้ว' }
const POINTS_REASON_MAP = { good_return: 'คืนตรงเวลา', community_service: 'จิตอาสา', report: 'แจ้งเบาะแส', weekly_bonus: 'โบนัสรายสัปดาห์', other: 'อื่นๆ' }

export default function MyManager() {
  const [tab, setTab] = useState('fav')
  const [error, setError] = useState('')

  const [favs, setFavs] = useState([])
  const [favForm, setFavForm] = useState(emptyFav)
  const [favEdit, setFavEdit] = useState(null)
  const [userFilter, setUserFilter] = useState('')

  const [pens, setPens] = useState([])
  const [penForm, setPenForm] = useState(emptyPen)
  const [penEdit, setPenEdit] = useState(null)

  const [lost, setLost] = useState([])
  const [lostForm, setLostForm] = useState(emptyLost)
  const [lostEdit, setLostEdit] = useState(null)

  const [pointsForm, setPointsForm] = useState(emptyPoints)
  const [pointsLog, setPointsLog] = useState([])

  useEffect(() => { loadAll() }, [])

async function loadAll() {
    setError('')
    try {
      const [favData, penData, lostData, ptData] = await Promise.all([
        favoritesApi.list(), penaltiesApi.list(), lostItemsApi.list(), pointsApi.list(),
      ])
      setFavs(favData); setPens(penData); setLost(lostData); setPointsLog(ptData)
    } catch (e) { setError(e.message) }
  }

  // ========== FAVORITES ==========
  async function submitFav(e) {
    e.preventDefault()
    try {
      const p = {
        user_id: favForm.user_id,
        target_type: favForm.target_type,
        bicycle_id: favForm.target_type === 'bicycle' ? favForm.bicycle_id : null,
        station_name: favForm.target_type === 'station' ? favForm.station_name : null,
        nickname: favForm.nickname || null,
      }
      if (favEdit) { await favoritesApi.update(favEdit, { nickname: favForm.nickname }) }
      else { await favoritesApi.create(p) }
      setFavForm(emptyFav); setFavEdit(null)
      const data = userFilter ? await favoritesApi.listByUser(Number(userFilter)) : await favoritesApi.list()
      setFavs(data)
    } catch (e) { setError(e.message) }
  }

  function editFav(r) {
    setFavEdit(r.id)
    setFavForm({ user_id: r.user_id, target_type: r.target_type, bicycle_id: r.bicycle_id || '', station_name: r.station_name || '', nickname: r.nickname || '' })
  }

  function cancelFav() { setFavForm(emptyFav); setFavEdit(null) }

  async function delFav(id) {
    if (!confirm('ลบรายการโปรดนี้?')) return
    try {
      await favoritesApi.delete(id)
      const data = userFilter ? await favoritesApi.listByUser(Number(userFilter)) : await favoritesApi.list()
      setFavs(data)
    } catch (e) { setError(e.message) }
  }

  function searchFav(e) { e.preventDefault(); loadFavs(userFilter) }
  async function loadFavs(uid) {
    try {
      const data = uid ? await favoritesApi.listByUser(Number(uid)) : await favoritesApi.list()
      setFavs(data)
    } catch (e) { setError(e.message) }
  }

  // ========== PENALTIES ==========
  async function submitPen(e) {
    e.preventDefault()
    try {
      const p = {
        user_id: penForm.user_id,
        reason: penForm.reason,
        penalty_points: Number(penForm.penalty_points),
        action: penForm.action,
        suspension_days: penForm.action === 'suspend' ? Number(penForm.suspension_days) : null,
        description: penForm.description || null,
        completed: penForm.completed,
      }
      if (penEdit) { await penaltiesApi.update(penEdit, p) }
      else { await penaltiesApi.create(p) }
      setPenForm(emptyPen); setPenEdit(null)
      const [pensData, ptData] = await Promise.all([penaltiesApi.list(), pointsApi.list()])
      setPens(pensData); setPointsLog(ptData)
    } catch (e) { setError(e.message) }
  }

  function editPen(r) {
    setPenEdit(r.id)
    setPenForm({ user_id: r.user_id, reason: r.reason, penalty_points: String(r.penalty_points), action: r.action, suspension_days: r.suspension_days || '', description: r.description || '', completed: r.completed })
  }

  function cancelPen() { setPenForm(emptyPen); setPenEdit(null) }

  async function delPen(id) {
    if (!confirm('ลบบทลงโทษนี้?')) return
    try { await penaltiesApi.delete(id); setPens(await penaltiesApi.list()) } catch (e) { setError(e.message) }
  }

  // ========== POINTS ==========
  async function submitPoints(e) {
    e.preventDefault()
    try {
      await pointsApi.add({
        user_id: pointsForm.user_id,
        points: Number(pointsForm.points),
        reason: pointsForm.reason,
        description: pointsForm.description || null,
      })
      setPointsForm(emptyPoints)
      setPointsLog(await pointsApi.list())
    } catch (e) { setError(e.message) }
  }

  // ========== LOST ITEMS ==========
  async function submitLost(e) {
    e.preventDefault()
    try {
      const p = {
        user_id: lostForm.user_id,
        bicycle_id: lostForm.bicycle_id,
        item_name: lostForm.item_name,
        location: lostForm.location || null,
        image_url: lostForm.image_url || null,
        description: lostForm.description || null,
        status: lostForm.status,
      }
      if (lostEdit) { await lostItemsApi.update(lostEdit, p) }
      else { await lostItemsApi.create(p) }
      setLostForm(emptyLost); setLostEdit(null)
      setLost(await lostItemsApi.list())
    } catch (e) { setError(e.message) }
  }

  function editLost(r) {
    setLostEdit(r.id)
    setLostForm({ user_id: r.user_id, bicycle_id: r.bicycle_id, item_name: r.item_name, location: r.location || '', image_url: r.image_url || '', description: r.description || '', status: r.status })
  }

  function cancelLost() { setLostForm(emptyLost); setLostEdit(null) }

  async function delLost(id) {
    if (!confirm('ลบรายการของหายนี้?')) return
    try { await lostItemsApi.delete(id); setLost(await lostItemsApi.list()) } catch (e) { setError(e.message) }
  }

  async function refreshLost() {
    try { setLost(await lostItemsApi.list()) } catch (e) { setError(e.message) }
  }

  return (
    <div className="manager">
      <h2>จัดการข้อมูลส่วนตัว</h2>
      {error && <p className="error" onClick={() => setError('')}>{error}</p>}

      <nav style={{ marginBottom: 16 }}>
        {[
          { key: 'fav', label: 'รายการโปรด' },
          { key: 'pen', label: 'บทลงโทษ' },
          { key: 'lost', label: 'ของหาย' },
        ].map(t => (
          <button key={t.key} className={tab === t.key ? 'active' : ''} onClick={() => setTab(t.key)}>{t.label}</button>
        ))}
      </nav>

      {/* ==================== รายการโปรด ==================== */}
      {tab === 'fav' && (
        <div>
          <form onSubmit={searchFav} className="filter-form">
            <label>ค้นหาตามรหัสผู้ใช้
              <input placeholder="เลข ID ผู้ใช้" value={userFilter} onChange={e => setUserFilter(e.target.value)} />
            </label>
            <button type="submit">ค้นหา</button>
            {userFilter && <button type="button" onClick={() => { setUserFilter(''); loadFavs('') }}>แสดงทั้งหมด</button>}
          </form>

          <form onSubmit={submitFav} className="form form-3col">
            {!favEdit && (
              <>
                <label>รหัสผู้ใช้ <input type="text" value={favForm.user_id} onChange={e => setFavForm({...favForm, user_id: e.target.value})} required placeholder="user001 หรือ 1" /></label>
                <label>ประเภท
                  <select value={favForm.target_type} onChange={e => setFavForm({...favForm, target_type: e.target.value})}>
                    <option value="bicycle">จักรยาน</option>
                    <option value="station">สถานี</option>
                  </select>
                </label>
                {favForm.target_type === 'bicycle' ? (
                  <label>รหัสจักรยาน <input type="text" value={favForm.bicycle_id} onChange={e => setFavForm({...favForm, bicycle_id: e.target.value})} required placeholder="BIKE001 หรือ 1" /></label>
                ) : (
                  <label>ชื่อสถานี <input value={favForm.station_name} onChange={e => setFavForm({...favForm, station_name: e.target.value})} required /></label>
                )}
              </>
            )}
            <label>ชื่อเล่น <input value={favForm.nickname} onChange={e => setFavForm({...favForm, nickname: e.target.value})} placeholder={favEdit ? 'ชื่อเล่นใหม่' : 'ไม่จำเป็น'} /></label>
            <div className="form-actions">
              <button type="submit">{favEdit ? 'อัปเดตชื่อเล่น' : 'เพิ่ม'}</button>
              {favEdit && <button type="button" onClick={cancelFav}>ยกเลิก</button>}
            </div>
          </form>

          <div className="table-wrap">
            <table>
              <thead><tr><th>ID</th><th>ผู้ใช้</th><th>ประเภท</th><th>รายการ</th><th>ชื่อเล่น</th><th>วันที่เพิ่ม</th><th>จัดการ</th></tr></thead>
              <tbody>
                {favs.map(f => (
                  <tr key={f.id}>
                    <td>{f.id}</td><td>#{f.user_id}</td>
                    <td>{f.target_type === 'bicycle' ? 'จักรยาน' : 'สถานี'}</td>
                    <td>{f.target_type === 'bicycle' ? `#${f.bicycle_id}` : f.station_name}</td>
                    <td>{f.nickname || '-'}</td>
                    <td>{new Date(f.created_at).toLocaleDateString('th-TH')}</td>
                    <td className="actions">
                      <button onClick={() => editFav(f)}>ตั้งชื่อเล่น</button>
                      <button className="danger" onClick={() => delFav(f.id)}>ลบ</button>
                    </td>
                  </tr>
                ))}
                {favs.length === 0 && <tr><td colSpan={7} style={{textAlign: 'center'}}>ไม่มีรายการโปรด</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ==================== บทลงโทษ (รวมแต้ม) ==================== */}
      {tab === 'pen' && (
        <div>
          <h3 style={{marginBottom:8}}>หักแต้ม (ทำผิด)</h3>
          <form onSubmit={submitPen} className="form form-3col">
            <label>รหัสผู้ใช้ <input type="text" value={penForm.user_id} onChange={e => setPenForm({...penForm, user_id: e.target.value})} required placeholder="user001 หรือ 1" /></label>
            <label>สาเหตุ
              <select value={penForm.reason} onChange={e => setPenForm({...penForm, reason: e.target.value})}>
                {Object.entries(REASON_MAP).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </label>
            <label>หักแต้ม <input type="number" value={penForm.penalty_points} onChange={e => setPenForm({...penForm, penalty_points: e.target.value})} /></label>
            <label>บทลงโทษ
              <select value={penForm.action} onChange={e => setPenForm({...penForm, action: e.target.value})}>
                {Object.entries(ACTION_MAP).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </label>
            {penForm.action === 'suspend' && (
              <label>จำนวนวัน <input type="number" value={penForm.suspension_days} onChange={e => setPenForm({...penForm, suspension_days: e.target.value})} /></label>
            )}
            <label>ดำเนินการแล้ว
              <select value={penForm.completed} onChange={e => setPenForm({...penForm, completed: e.target.value === 'true'})}>
                <option value={false}>ยังไม่ดำเนินการ</option>
                <option value={true}>ดำเนินการแล้ว</option>
              </select>
            </label>
            <label style={{gridColumn: '1 / -1'}}>รายละเอียด <textarea rows={2} value={penForm.description} onChange={e => setPenForm({...penForm, description: e.target.value})} placeholder="รายละเอียด..." /></label>
            <div className="form-actions">
              <button type="submit">{penEdit ? 'อัปเดต' : 'เพิ่ม'}</button>
              {penEdit && <button type="button" onClick={cancelPen}>ยกเลิก</button>}
            </div>
          </form>

          <hr style={{margin:'20px 0'}} />

          <h3 style={{marginBottom:8}}>เพิ่มแต้ม (ทำดี)</h3>
          <form onSubmit={submitPoints} className="form form-3col">
            <label>รหัสผู้ใช้ <input type="text" value={pointsForm.user_id} onChange={e => setPointsForm({...pointsForm, user_id: e.target.value})} required placeholder="user001 หรือ 1" /></label>
            <label>จำนวนแต้ม <input type="number" value={pointsForm.points} onChange={e => setPointsForm({...pointsForm, points: e.target.value})} required /></label>
            <label>สาเหตุ
              <select value={pointsForm.reason} onChange={e => setPointsForm({...pointsForm, reason: e.target.value})}>
                {Object.entries(POINTS_REASON_MAP).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </label>
            <label style={{gridColumn: '1 / -1'}}>รายละเอียด <textarea rows={2} value={pointsForm.description} onChange={e => setPointsForm({...pointsForm, description: e.target.value})} placeholder="บันทึก..." /></label>
            <div className="form-actions">
              <button type="submit">เพิ่มแต้ม</button>
            </div>
          </form>

          <hr style={{margin:'20px 0'}} />

          <h3 style={{marginBottom:8}}>ประวัติแต้มทั้งหมด</h3>
          <div className="table-wrap">
            <table>
              <thead><tr><th>ID</th><th>ผู้ใช้</th><th>แต้ม</th><th>สาเหตุ</th><th>รายละเอียด</th><th>วันที่</th></tr></thead>
              <tbody>
                {pointsLog.map(p => (
                  <tr key={p.id}>
                    <td>{p.id}</td><td>#{p.user_id}</td>
                    <td style={{color: p.points > 0 ? 'green' : 'red', fontWeight: 'bold'}}>{p.points > 0 ? `+${p.points}` : p.points}</td>
                    <td>{POINTS_REASON_MAP[p.reason] || REASON_MAP[p.reason] || p.reason}</td>
                    <td>{p.description || '-'}</td>
                    <td>{new Date(p.created_at).toLocaleDateString('th-TH')}</td>
                  </tr>
                ))}
                {pointsLog.length === 0 && <tr><td colSpan={6} style={{textAlign: 'center'}}>ไม่มีประวัติ</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ==================== ของหาย ==================== */}
      {tab === 'lost' && (
        <div>
          <form onSubmit={submitLost} className="form form-3col">
            <label>รหัสผู้ใช้ <input type="text" value={lostForm.user_id} onChange={e => setLostForm({...lostForm, user_id: e.target.value})} required placeholder="user001 หรือ 1" /></label>
            <label>รหัสจักรยาน <input type="text" value={lostForm.bicycle_id} onChange={e => setLostForm({...lostForm, bicycle_id: e.target.value})} required placeholder="BIKE001 หรือ 1" /></label>
            <label>ชื่อสิ่งของ <input value={lostForm.item_name} onChange={e => setLostForm({...lostForm, item_name: e.target.value})} required placeholder="เช่น กระบอกน้ำ, หมวกกันน็อค" /></label>
            <label>สถานที่ที่หาย <input value={lostForm.location} onChange={e => setLostForm({...lostForm, location: e.target.value})} placeholder="เช่น สถานีศูนย์กีฬา" /></label>
            <label>URL รูปภาพ <input value={lostForm.image_url} onChange={e => setLostForm({...lostForm, image_url: e.target.value})} placeholder="https://..." /></label>
            <label>สถานะ
              <select value={lostForm.status} onChange={e => setLostForm({...lostForm, status: e.target.value})}>
                {Object.entries(LOST_STATUS_MAP).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </label>
            <label style={{gridColumn: '1 / -1'}}>รายละเอียด <textarea rows={2} value={lostForm.description} onChange={e => setLostForm({...lostForm, description: e.target.value})} placeholder="รายละเอียดเพิ่มเติม..." /></label>
            <div className="form-actions">
              <button type="submit">{lostEdit ? 'อัปเดต' : 'เพิ่ม'}</button>
              {lostEdit && <button type="button" onClick={cancelLost}>ยกเลิก</button>}
            </div>
          </form>

          <div className="table-wrap">
            <table>
              <thead><tr><th>ID</th><th>ผู้ใช้</th><th>จักรยาน</th><th>ชื่อสิ่งของ</th><th>สถานที่</th><th>รูป</th><th>รายละเอียด</th><th>สถานะ</th><th>วันที่แจ้ง</th><th>จัดการ</th></tr></thead>
              <tbody>
                {lost.map(r => (
                  <tr key={r.id}>
                    <td>{r.id}</td><td>#{r.user_id}</td>
                    <td>#{r.bicycle_id}</td>
                    <td>{r.item_name}</td>
                    <td>{r.location || '-'}</td>
                    <td>{r.image_url ? <a href={r.image_url} target="_blank" rel="noreferrer">ดูรูป</a> : '-'}</td>
                    <td>{r.description || '-'}</td>
                    <td>{LOST_STATUS_MAP[r.status] || r.status}</td>
                    <td>{r.created_at ? new Date(r.created_at).toLocaleDateString('th-TH') : '-'}</td>
                    <td className="actions">
                      <button onClick={() => editLost(r)}>แก้ไข</button>
                      <button className="danger" onClick={() => delLost(r.id)}>ลบ</button>
                    </td>
                  </tr>
                ))}
                {lost.length === 0 && <tr><td colSpan={10} style={{textAlign: 'center'}}>ไม่มีของหาย</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}