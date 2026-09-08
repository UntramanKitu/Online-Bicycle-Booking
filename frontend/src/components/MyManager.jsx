import { useState, useEffect } from 'react'
import { favoritesApi, penaltiesApi, lostItemsApi, usersApi, getActor, setActor } from '../api'

const emptyFav = { user_id: '', target_type: 'bicycle', bicycle_id: '', station_name: '', nickname: '' }
const emptyPen = { user_id: '', reason: 'late_return', action: 'warning', suspension_days: '', description: '', completed: false }
const emptyLost = { user_id: '', item_name: '', location: '', image_url: '', description: '', status: 'lost' }

// เงื่อนไขที่ "เพิ่ม" คะแนน (+1) — นอกนั้นทั้งหมดคือ "หัก" คะแนน (-1) ทิศทางคำนวณจาก reason
// ล้วนๆ ผู้ใช้ไม่ต้องเลือกเอง (ต้องตรงกับ POSITIVE_REASONS ฝั่ง backend/routers/penalties.py)
const POSITIVE_REASONS = ['good_behavior', 'no_violation_week']
// no_violation_week ให้ระบบสร้างเองผ่านปุ่ม "ตรวจโบนัสประจำสัปดาห์" เท่านั้น ไม่ให้เลือกตอนสร้างเอง
const REASON_OPTIONS = ['late_return', 'damaged', 'lost', 'other', 'good_behavior']
const REASON_MAP = {
  late_return: 'คืนช้า (-1)', damaged: 'เสียหาย (-1)', lost: 'สูญหาย (-1)', other: 'อื่นๆ (-1)',
  good_behavior: 'พฤติกรรมดี (+1)', no_violation_week: 'ไม่ทำผิดครบ 7 วัน (+1, อัตโนมัติ)',
}
const ACTION_MAP = { warning: 'เตือน', service: 'จิตอาสา', suspend: 'งดยืม', reward: 'ให้คะแนนคืน' }
const LOST_STATUS_MAP = { lost: 'สูญหาย', found: 'พบแล้ว' }

export default function MyManager() {
  const [tab, setTab] = useState('fav')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  function notify(msg) {
    setSuccess(msg)
    setTimeout(() => setSuccess(''), 3000)
  }

  // ========== ระบุตัวตนแบบง่าย (ยังไม่มี login จริง) ==========
  const [actor, setActorState] = useState(getActor())
  const [identityInput, setIdentityInput] = useState('')
  const [identityBusy, setIdentityBusy] = useState(false)
  const isAdmin = actor.role === 'admin'
  const isMe = (userId) => actor.role === 'admin' || String(userId) === String(actor.userId)

  // รหัสผ่านแอดมินแบบง่าย — เช็คแค่ฝั่งหน้าเว็บเท่านั้น ไม่ใช่ระบบความปลอดภัยจริง
  // (เหมือนที่คุยกันไว้: กันกดพลาด/สลับโหมดเล่นๆ ไม่ใช่กันคนตั้งใจแฮ็ก ต้องรอ login จริง
  // ถึงจะปิดช่องนี้ได้สมบูรณ์)
  const ADMIN_PASSWORD = '1234'
  const [showAdminPrompt, setShowAdminPrompt] = useState(false)
  const [adminPasswordInput, setAdminPasswordInput] = useState('')

  function switchToAdmin() {
    const next = { role: 'admin', userId: '', username: '' }
    setActor(next); setActorState(next)
  }

  function requestAdminMode() {
    if (isAdmin) return
    setShowAdminPrompt(true)
    setAdminPasswordInput('')
  }

  function submitAdminPassword(e) {
    e.preventDefault()
    if (adminPasswordInput === ADMIN_PASSWORD) {
      switchToAdmin()
      setShowAdminPrompt(false)
    } else {
      setError('รหัสผ่านแอดมินไม่ถูกต้อง')
    }
  }

  function switchToUserMode() {
    setShowAdminPrompt(false)
    const next = { role: 'user', userId: '', username: '' }
    setActor(next); setActorState(next)
  }

  async function confirmIdentity(e) {
    e.preventDefault()
    setIdentityBusy(true)
    setError('')
    try {
      const u = await usersApi.resolve(identityInput.trim())
      const next = { role: 'user', userId: u.id, username: u.username }
      setActor(next); setActorState(next)
      setIdentityInput('')
      notify(`ยืนยันตัวตนเป็น ${u.username} เรียบร้อยแล้ว`)
    } catch (e) { setError(e.message) }
    finally { setIdentityBusy(false) }
  }

  function clearIdentity() {
    const next = { role: 'user', userId: '', username: '' }
    setActor(next); setActorState(next)
  }

  // โหมดผู้ใช้ทั่วไป: ฟอร์มเพิ่มข้อมูลใหม่ต้องเป็น "ของตัวเอง" เสมอ ล็อกช่อง user_id ไว้
  function defaultFormFor(empty) {
    return actor.role === 'user' ? { ...empty, user_id: String(actor.userId || '') } : empty
  }

  const [favs, setFavs] = useState([])
  const [favForm, setFavForm] = useState(() => defaultFormFor(emptyFav))
  const [favEdit, setFavEdit] = useState(null)
  const [userFilter, setUserFilter] = useState('')

  const [pens, setPens] = useState([])
  const [penForm, setPenForm] = useState(emptyPen)
  const [penEdit, setPenEdit] = useState(null)

  const [lost, setLost] = useState([])
  const [lostForm, setLostForm] = useState(() => defaultFormFor(emptyLost))
  const [lostEdit, setLostEdit] = useState(null)

  useEffect(() => { loadAll() }, [actor.role, actor.userId])

  async function loadAll() {
    setError('')
    setLoading(true)
    try {
      const scopedToSelf = actor.role === 'user'
      if (scopedToSelf && !actor.userId) {
        // โหมดผู้ใช้ทั่วไปแต่ยังไม่ได้ยืนยันตัวตน — ยังไม่รู้ว่า "ของตัวเอง" คืออันไหน
        setFavs([]); setPens([]); setLost(await lostItemsApi.list())
        return
      }
      const favPromise = scopedToSelf ? favoritesApi.listByUser(actor.userId) : favoritesApi.list()
      const penPromise = scopedToSelf ? penaltiesApi.listByUser(actor.userId) : penaltiesApi.list()
      const [favData, penData, lostData] = await Promise.all([favPromise, penPromise, lostItemsApi.list()])
      setFavs(favData); setPens(penData); setLost(lostData)
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  // ========== FAVORITES ==========
  async function reloadFavs() {
    if (actor.role === 'user') { setFavs(actor.userId ? await favoritesApi.listByUser(actor.userId) : []); return }
    setFavs(userFilter ? await favoritesApi.listByUser(Number(userFilter)) : await favoritesApi.list())
  }

  async function submitFav(e) {
    e.preventDefault()
    setSaving(true)
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
      setFavForm(defaultFormFor(emptyFav)); setFavEdit(null)
      await reloadFavs()
      notify(favEdit ? 'อัปเดตชื่อเล่นเรียบร้อยแล้ว' : 'เพิ่มรายการโปรดเรียบร้อยแล้ว')
    } catch (e) { setError(e.message) }
    finally { setSaving(false) }
  }

  function editFav(r) {
    setFavEdit(r.id)
    setFavForm({ user_id: r.user_id, target_type: r.target_type, bicycle_id: r.bicycle_id || '', station_name: r.station_name || '', nickname: r.nickname || '' })
  }

  function cancelFav() { setFavForm(defaultFormFor(emptyFav)); setFavEdit(null) }

  async function delFav(id) {
    if (!confirm('ลบรายการโปรดนี้?')) return
    try {
      await favoritesApi.delete(id)
      await reloadFavs()
      notify('ลบรายการโปรดเรียบร้อยแล้ว')
    } catch (e) { setError(e.message) }
  }

  function searchFav(e) { e.preventDefault(); loadFavs(userFilter) }
  async function loadFavs(uid) {
    try {
      const data = uid ? await favoritesApi.listByUser(Number(uid)) : await favoritesApi.list()
      setFavs(data)
    } catch (e) { setError(e.message) }
  }

  // ========== PENALTIES (แอดมินเท่านั้นที่สร้าง/แก้/ลบได้ — ดู UI ด้านล่าง) ==========
  async function reloadPens() {
    setPens(actor.role === 'user' ? (actor.userId ? await penaltiesApi.listByUser(actor.userId) : []) : await penaltiesApi.list())
  }

  async function submitPen(e) {
    e.preventDefault()
    setSaving(true)
    try {
      const p = {
        user_id: penForm.user_id,
        reason: penForm.reason,
        penalty_points: 1, // ขนาดตรึงไว้ที่ 1 เสมอ ทิศทาง +/- คำนวณจาก reason ที่ backend
        action: penForm.action,
        suspension_days: penForm.action === 'suspend' ? Number(penForm.suspension_days) : null,
        description: penForm.description || null,
        completed: penForm.completed,
      }
      if (penEdit) { await penaltiesApi.update(penEdit, p) }
      else { await penaltiesApi.create(p) }
      setPenForm(emptyPen); setPenEdit(null)
      await reloadPens()
      notify(penEdit ? 'อัปเดตรายการเรียบร้อยแล้ว' : (POSITIVE_REASONS.includes(p.reason) ? 'บันทึกและเพิ่มคะแนนเรียบร้อยแล้ว' : 'บันทึกและหักคะแนนเรียบร้อยแล้ว'))
    } catch (e) { setError(e.message) }
    finally { setSaving(false) }
  }

  function editPen(r) {
    setPenEdit(r.id)
    setPenForm({ user_id: r.user_id, reason: r.reason, action: r.action, suspension_days: r.suspension_days || '', description: r.description || '', completed: r.completed })
  }

  function cancelPen() { setPenForm(emptyPen); setPenEdit(null) }

  async function applyWeeklyBonus() {
    setSaving(true)
    try {
      const awarded = await penaltiesApi.applyWeeklyBonus()
      await reloadPens()
      notify(awarded.length ? `ให้คะแนนคืนอัตโนมัติ ${awarded.length} คนเรียบร้อยแล้ว` : 'ไม่มีใครเข้าเงื่อนไขได้คะแนนคืนรอบนี้')
    } catch (e) { setError(e.message) }
    finally { setSaving(false) }
  }

  async function delPen(id) {
    if (!confirm('ลบรายการนี้?')) return
    try { await penaltiesApi.delete(id); await reloadPens(); notify('ลบบทลงโทษเรียบร้อยแล้ว') } catch (e) { setError(e.message) }
  }

  // ========== LOST ITEMS ==========
  async function submitLost(e) {
    e.preventDefault()
    setSaving(true)
    try {
      const p = {
        user_id: lostForm.user_id,
        item_name: lostForm.item_name,
        location: lostForm.location || null,
        image_url: lostForm.image_url || null,
        description: lostForm.description || null,
        status: lostForm.status,
      }
      if (lostEdit) { await lostItemsApi.update(lostEdit, p) }
      else { await lostItemsApi.create(p) }
      setLostForm(defaultFormFor(emptyLost)); setLostEdit(null)
      setLost(await lostItemsApi.list())
      notify(lostEdit ? 'อัปเดตรายการของหายเรียบร้อยแล้ว' : 'แจ้งของหายเรียบร้อยแล้ว')
    } catch (e) { setError(e.message) }
    finally { setSaving(false) }
  }

  function editLost(r) {
    setLostEdit(r.id)
    setLostForm({ user_id: r.user_id, item_name: r.item_name, location: r.location || '', image_url: r.image_url || '', description: r.description || '', status: r.status })
  }

  function cancelLost() { setLostForm(defaultFormFor(emptyLost)); setLostEdit(null) }

  async function delLost(id) {
    if (!confirm('ลบรายการของหายนี้?')) return
    try { await lostItemsApi.delete(id); setLost(await lostItemsApi.list()); notify('ลบรายการของหายเรียบร้อยแล้ว') } catch (e) { setError(e.message) }
  }

  async function refreshLost() {
    try { setLost(await lostItemsApi.list()) } catch (e) { setError(e.message) }
  }

  return (
    <div className="manager">
      <h2>จัดการข้อมูลส่วนตัว</h2>
      {error && <p className="error" onClick={() => setError('')} title="คลิกเพื่อปิด">⚠ {error}</p>}
      {success && <p className="success-msg" onClick={() => setSuccess('')} title="คลิกเพื่อปิด">✓ {success}</p>}

      {/* ==================== แถบระบุตัวตน/สลับโหมด (ยังไม่มี login จริง) ==================== */}
      <div className="identity-bar">
        <div>
          <button type="button" className={!isAdmin ? 'active' : ''} onClick={switchToUserMode}>ผู้ใช้ทั่วไป</button>{' '}
          <button type="button" className={isAdmin ? 'active' : ''} onClick={requestAdminMode}>แอดมิน</button>
        </div>
        {isAdmin ? (
          <span style={{ color: 'green' }}>🔓 โหมดแอดมิน — จัดการข้อมูลทุกคนได้เต็มสิทธิ์</span>
        ) : showAdminPrompt ? (
          <form onSubmit={submitAdminPassword} style={{ display: 'flex', gap: 8 }}>
            <span>รหัสผ่านแอดมิน:</span>
            <input type="password" autoFocus value={adminPasswordInput} onChange={e => setAdminPasswordInput(e.target.value)} placeholder="••••" />
            <button type="submit">เข้าสู่โหมดแอดมิน</button>
            <button type="button" onClick={() => setShowAdminPrompt(false)}>ยกเลิก</button>
          </form>
        ) : actor.userId ? (
          <span>👤 กำลังใช้งานในชื่อ <b>{actor.username}</b> (#{actor.userId}) — แก้ไข/ลบได้เฉพาะของตัวเอง{' '}
            <button type="button" onClick={clearIdentity}>ออกจากระบบ</button>
          </span>
        ) : (
          <form onSubmit={confirmIdentity} style={{ display: 'flex', gap: 8 }}>
            <span>ยังไม่ได้ยืนยันตัวตน:</span>
            <input placeholder="user001 หรือ 1" value={identityInput} onChange={e => setIdentityInput(e.target.value)} required />
            <button type="submit" disabled={identityBusy}>{identityBusy ? 'กำลังตรวจสอบ...' : 'ยืนยันตัวตน'}</button>
          </form>
        )}
      </div>

      <nav style={{ marginBottom: 16 }}>
        {[
          { key: 'fav', icon: '⭐', label: 'รายการโปรด', count: favs.length },
          { key: 'pen', icon: '⚖️', label: 'คะแนน/บทลงโทษ', count: pens.length },
          { key: 'lost', icon: '📦', label: 'พบของหล่นหาย', count: lost.length },
        ].map(t => (
          <button key={t.key} className={tab === t.key ? 'active' : ''} onClick={() => setTab(t.key)}>
            <span>{t.icon}</span> {t.label}{!loading && ` (${t.count})`}
          </button>
        ))}
      </nav>

      {loading && <p className="loading-msg">กำลังโหลดข้อมูล...</p>}

      {/* ==================== รายการโปรด ==================== */}
      {tab === 'fav' && (
        <div>
          {isAdmin && (
            <div className="section">
              <div className="section-title">🔍 ค้นหารายการโปรดตามผู้ใช้</div>
              <div className="section-body">
                <form onSubmit={searchFav} className="filter-form">
                  <label>รหัสผู้ใช้
                    <input placeholder="เลข ID ผู้ใช้" value={userFilter} onChange={e => setUserFilter(e.target.value)} />
                  </label>
                  <button type="submit">ค้นหา</button>
                  {userFilter && <button type="button" onClick={() => { setUserFilter(''); loadFavs('') }}>แสดงทั้งหมด</button>}
                </form>
              </div>
            </div>
          )}

          <div className="section">
            <div className="section-title">{favEdit ? '✏️ แก้ไขชื่อเล่น' : '➕ เพิ่มรายการโปรด'}</div>
            <div className="section-body">
              {!isAdmin && !actor.userId && <p className="hint">* ยืนยันตัวตนที่แถบด้านบนก่อน ถึงจะเพิ่ม/ดูรายการโปรดของตัวเองได้</p>}
              <p className="hint">* ช่อง "รหัสผู้ใช้"/"รหัสจักรยาน" กรอกได้ทั้งเลข ID (เช่น 1) หรือ username/รหัสจักรยาน (เช่น user001, BIKE001)</p>
              <form onSubmit={submitFav} className="form form-3col">
                {!favEdit && (
                  <>
                    {isAdmin && (
                      <label>รหัสผู้ใช้ <input type="text" value={favForm.user_id} onChange={e => setFavForm({...favForm, user_id: e.target.value})} required placeholder="user001 หรือ 1" /></label>
                    )}
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
                  <button type="submit" disabled={saving}>{saving ? 'กำลังบันทึก...' : favEdit ? 'อัปเดตชื่อเล่น' : 'เพิ่ม'}</button>
                  {favEdit && <button type="button" onClick={cancelFav} disabled={saving}>ยกเลิก</button>}
                </div>
              </form>
            </div>
          </div>

          <div className="section">
            <div className="section-title">📋 รายการโปรดทั้งหมด <span className="count">{favs.length} รายการ</span></div>
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
                        {isMe(f.user_id) ? (
                          <>
                            <button onClick={() => editFav(f)}>ตั้งชื่อเล่น</button>
                            <button className="danger" onClick={() => delFav(f.id)}>ลบ</button>
                          </>
                        ) : <span style={{color: '#999'}}>ไม่ใช่ของคุณ</span>}
                      </td>
                    </tr>
                  ))}
                  {favs.length === 0 && <tr><td colSpan={7} style={{textAlign: 'center'}}>ไม่มีรายการโปรด</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ==================== คะแนน/บทลงโทษ ==================== */}
      {tab === 'pen' && (
        <div>
          {isAdmin ? (
            <div className="section">
              <div className="section-title">
                {penEdit ? '✏️ แก้ไขรายการ' : '➕ บันทึกคะแนนความประพฤติ (+1 / -1)'}
                {!penEdit && (
                  <button type="button" onClick={applyWeeklyBonus} disabled={saving}>
                    ↻ ตรวจ+ให้คะแนนคืนประจำสัปดาห์
                  </button>
                )}
              </div>
              <div className="section-body">
                <p className="hint">* ช่อง "รหัสผู้ใช้" กรอกได้ทั้งเลข ID (เช่น 1) หรือ username (เช่น user001)</p>
                <p className="hint">* ทิศทาง +1/-1 คำนวณจาก "สาเหตุ" อัตโนมัติ — เลือกสาเหตุที่ตรงกับเหตุการณ์จริงเท่านั้น ไม่ต้องพิมพ์จำนวนแต้มเอง</p>
                <form onSubmit={submitPen} className="form form-3col">
                  <label>รหัสผู้ใช้ <input type="text" value={penForm.user_id} onChange={e => setPenForm({...penForm, user_id: e.target.value})} required placeholder="user001 หรือ 1" /></label>
                  <label>สาเหตุ
                    <select value={penForm.reason} onChange={e => setPenForm({...penForm, reason: e.target.value})}>
                      {REASON_OPTIONS.map(k => <option key={k} value={k}>{REASON_MAP[k]}</option>)}
                    </select>
                  </label>
                  <label>ผลต่อคะแนน
                    <input type="text" readOnly value={POSITIVE_REASONS.includes(penForm.reason) ? '+1 (เพิ่มคะแนน)' : '-1 (หักคะแนน)'}
                      style={{ color: POSITIVE_REASONS.includes(penForm.reason) ? 'green' : 'red', fontWeight: 'bold' }} />
                  </label>
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
                    <button type="submit" disabled={saving}>{saving ? 'กำลังบันทึก...' : penEdit ? 'อัปเดต' : 'เพิ่ม'}</button>
                    {penEdit && <button type="button" onClick={cancelPen} disabled={saving}>ยกเลิก</button>}
                  </div>
                </form>
              </div>
            </div>
          ) : (
            <p className="hint">* โหมดผู้ใช้ทั่วไปดูได้อย่างเดียว (เฉพาะของตัวเอง) — ออกบทลงโทษ/ให้คะแนนได้เฉพาะแอดมินเท่านั้น</p>
          )}

          <div className="section">
            <div className="section-title">📋 ประวัติคะแนน <span className="count">{pens.length} รายการ</span></div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>ID</th><th>ผู้ใช้</th><th>สาเหตุ</th><th>คะแนน</th><th>บทลงโทษ</th><th>สถานะ</th><th>วันที่</th>{isAdmin && <th>จัดการ</th>}</tr></thead>
                <tbody>
                  {pens.map(p => {
                    const isPositive = POSITIVE_REASONS.includes(p.reason)
                    return (
                    <tr key={p.id}>
                      <td>{p.id}</td><td>#{p.user_id}</td>
                      <td>{REASON_MAP[p.reason] || p.reason}</td>
                      <td style={{color: isPositive ? 'green' : 'red', fontWeight: 'bold'}}>{isPositive ? '+' : '-'}{p.penalty_points}</td>
                      <td>{ACTION_MAP[p.action] || p.action}{p.action === 'suspend' && p.suspension_days ? ` (${p.suspension_days} วัน)` : ''}</td>
                      <td>{p.completed ? 'ดำเนินการแล้ว' : 'ยังไม่ดำเนินการ'}</td>
                      <td>{new Date(p.created_at).toLocaleDateString('th-TH')}</td>
                      {isAdmin && (
                        <td className="actions">
                          <button onClick={() => editPen(p)}>แก้ไข</button>
                          <button className="danger" onClick={() => delPen(p.id)}>ลบ</button>
                        </td>
                      )}
                    </tr>
                  )})}
                  {pens.length === 0 && (
                    <tr><td colSpan={isAdmin ? 8 : 7} style={{textAlign: 'center'}}>
                      {!isAdmin && !actor.userId ? 'ยืนยันตัวตนที่แถบด้านบนก่อน' : 'ไม่มีรายการ'}
                    </td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ==================== ของหาย ==================== */}
      {tab === 'lost' && (
        <div>
          <div className="section">
            <div className="section-title">{lostEdit ? '✏️ แก้ไขรายการของหาย' : '➕ แจ้งของหาย'}</div>
            <div className="section-body">
              {!isAdmin && !actor.userId && <p className="hint">* ยืนยันตัวตนที่แถบด้านบนก่อน ถึงจะแจ้งของหายในนามตัวเองได้ (ดูรายการทั้งหมดได้อยู่แล้วโดยไม่ต้องยืนยันตัวตน)</p>}
              <p className="hint">* ช่อง "รหัสผู้ใช้" กรอกได้ทั้งเลข ID (เช่น 1) หรือ username (เช่น user001)</p>
              <form onSubmit={submitLost} className="form form-3col">
                {isAdmin && (
                  <label>รหัสผู้ใช้ <input type="text" value={lostForm.user_id} onChange={e => setLostForm({...lostForm, user_id: e.target.value})} required placeholder="user001 หรือ 1" /></label>
                )}
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
                  <button type="submit" disabled={saving}>{saving ? 'กำลังบันทึก...' : lostEdit ? 'อัปเดต' : 'เพิ่ม'}</button>
                  {lostEdit && <button type="button" onClick={cancelLost} disabled={saving}>ยกเลิก</button>}
                </div>
              </form>
            </div>
          </div>

          <div className="section">
            <div className="section-title">📋 รายการของหายทั้งหมด <span className="count">{lost.length} รายการ</span>
              <button type="button" onClick={refreshLost}>↻ รีเฟรช</button>
            </div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>ID</th><th>ผู้ใช้</th><th>ชื่อสิ่งของ</th><th>สถานที่</th><th>รูป</th><th>รายละเอียด</th><th>สถานะ</th><th>วันที่แจ้ง</th><th>จัดการ</th></tr></thead>
                <tbody>
                  {lost.map(r => (
                    <tr key={r.id}>
                      <td>{r.id}</td><td>#{r.user_id}</td>
                      <td>{r.item_name}</td>
                      <td>{r.location || '-'}</td>
                      <td>{r.image_url ? <a href={r.image_url} target="_blank" rel="noreferrer">ดูรูป</a> : '-'}</td>
                      <td>{r.description || '-'}</td>
                      <td>{LOST_STATUS_MAP[r.status] || r.status}</td>
                      <td>{r.created_at ? new Date(r.created_at).toLocaleDateString('th-TH') : '-'}</td>
                      <td className="actions">
                        {isMe(r.user_id) ? (
                          <>
                            <button onClick={() => editLost(r)}>แก้ไข</button>
                            <button className="danger" onClick={() => delLost(r.id)}>ลบ</button>
                          </>
                        ) : <span style={{color: '#999'}}>ไม่ใช่ของคุณ</span>}
                      </td>
                    </tr>
                  ))}
                  {lost.length === 0 && <tr><td colSpan={9} style={{textAlign: 'center'}}>ไม่มีของหาย</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}