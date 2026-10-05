import { useEffect, useRef, useState } from 'react'
import { api, getApiError } from '../../../api'
import { formatDateTime, toIso } from '../../../utils'
import { BOOKING_STATUSES } from '../../../constants'
import { useCurrentUser } from '../../../context/currentUser'
import Stars from '../../../components/Stars'
import { Time24 } from '../../../components/Time24'
// ฟีเจอร์ mock (รายการโปรด / แจ้งของหาย) — แยกออกมาเป็น modules/akeapon (ยังไม่เชื่อม backend)
import { useFavorites } from '../../akeapon/favorites'
import { useLostItems } from '../../akeapon/lostItems'
import FavoriteButton from '../../akeapon/components/FavoriteButton'
import FavoritesFilter from '../../akeapon/components/FavoritesFilter'
import LostItemModal from '../../akeapon/components/LostItemModal'
import LostItemHistory from '../../akeapon/components/LostItemHistory'

// เวลา HH:MM เริ่มต้นสำหรับช่องเลือกเวลา = อีก 1 ชม. ข้างหน้า
function defaultLaterTime() {
  const d = new Date(Date.now() + 60 * 60 * 1000)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function BikeIcon() {
  return <svg className="bike-illustration" width="64" height="40" viewBox="0 0 64 40" fill="none" aria-hidden="true">
    <circle cx="12" cy="30" r="8" />
    <circle cx="50" cy="30" r="8" />
    <path d="M12 30 24 12h12L26 30M32 12l18 18M20 12h14M24 12l-4-6" />
  </svg>
}

export default function BookingsPage() {
  const { userId, currentUser, usersLoading, isAdmin, getUserName } = useCurrentUser()
  const [bikes, setBikes] = useState([])
  const [myBookings, setMyBookings] = useState([])
  // มุมมองของแอดมิน: mine = ของตัวเอง (default), all = การจองทุกคนในระบบ
  const [scope, setScope] = useState('mine')
  const [loading, setLoading] = useState(true)
  const [selectedBike, setSelectedBike] = useState(null)
  const [duration, setDuration] = useState('30')
  const [pickupTime, setPickupTime] = useState('now')
  const [laterTime, setLaterTime] = useState('')   // HH:MM สำหรับรับรถล่วงหน้า
  const [timeError, setTimeError] = useState(null)
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [message, setMessage] = useState(null)
  // popup ให้คะแนน — เปิดอัตโนมัติหลังคืนรถสำเร็จ
  const [reviewFor, setReviewFor] = useState(null)
  const [reviewRating, setReviewRating] = useState(5)
  const [reviewComment, setReviewComment] = useState('')
  const [reviewSaving, setReviewSaving] = useState(false)
  // ฟอร์มแจ้งซ่อมจากหน้าจอง (ผูกกับจักรยานคันนั้น)
  const [reportFor, setReportFor] = useState(null)
  const [reportIssue, setReportIssue] = useState('')
  const [reportDesc, setReportDesc] = useState('')
  const [reportSaving, setReportSaving] = useState(false)
  // เตือนใกล้ถึงเวลารับรถ (15 นาทีก่อน)
  const [pickupReminder, setPickupReminder] = useState(null)
  const notifiedReminders = useRef(new Set())
  // mock: รายการโปรด + แจ้งของหาย — แยก logic ไว้ที่ modules/akeapon (localStorage ยังไม่เชื่อม backend)
  const { favorites, favOnly, setFavOnly, toggleFavorite } = useFavorites()
  const { lostItems, lostFor, openLost, closeLost, saveLostItem } = useLostItems()

  async function load(nextScope = scope) {
    setLoading(true)
    try {
      const [bicycleRes, bookingRes] = await Promise.all([
        api.get('/bicycles'),
        nextScope === 'all' && isAdmin
          ? api.get('/bookings') // แอดมิน: การจองของผู้ใช้ทุกคน (ไม่ส่ง user_id)
          : api.get('/bookings', { params: { user_id: userId } }),
      ])
      setBikes(bicycleRes.data)
      setMyBookings(bookingRes.data)
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (usersLoading || !userId) return
    const timer = window.setTimeout(() => load(scope), 0)
    return () => window.clearTimeout(timer)
  }, [userId, usersLoading, scope]) // eslint-disable-line react-hooks/exhaustive-deps

  function switchScope(next) {
    if (next === scope) return
    setMessage(null)
    setScope(next)
  }

  // แปลง bicycle_id เป็นชื่อจักรยาน สำหรับรายการใน "การจองของฉัน"
  const getBikeName = (id) => {
    const found = bikes.find((b) => b.id === Number(id))
    return found ? found.model : `จักรยาน #${id}`
  }

  // เตือนเมื่อใกล้ถึงเวลารับรถ (ภายใน 15 นาที) — พร้อมสร้าง notification ให้กระดิ่งนับด้วย (ครั้งเดียวต่อการจอง)
  useEffect(() => {
    const check = () => {
      const now = Date.now()
      const soon = myBookings
        .filter((b) => ['pending', 'confirmed'].includes(b.status))
        .filter((b) => {
          const t = new Date(b.start_time).getTime()
          return Number.isFinite(t) && t > now && t - now <= 15 * 60 * 1000
        })
        .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
      if (soon.length > 0) {
        setPickupReminder(soon[0])
        const b = soon[0]
        if (userId && !notifiedReminders.current.has(b.id)) {
          notifiedReminders.current.add(b.id)
          api
            .post('/notifications', {
              user_id: userId,
              title: 'ใกล้ถึงเวลารับรถแล้ว',
              message: `อีกไม่เกิน 15 นาที ถึงเวลารับ ${getBikeName(b.bicycle_id)} ที่ ${b.pickup_location || 'จุดรับรถ'}`,
            })
            .catch(() => { /* สร้างแจ้งเตือนไม่ได้ไม่เป็นไร — banner ยังขึ้น */ })
        }
      } else {
        setPickupReminder(null)
      }
    }
    check()
    const timer = window.setInterval(check, 30000)
    return () => window.clearInterval(timer)
  }, [myBookings, userId]) // eslint-disable-line react-hooks/exhaustive-deps

  // mock: บันทึกการแจ้งของหาย (modules/akeapon — localStorage ยังไม่เชื่อม backend)
  function handleLostSaved(entry) {
    saveLostItem(entry)
    setMessage({ type: 'success', text: 'บันทึกการแจ้งของหายแล้ว (ข้อมูลจำลอง — ยังไม่ส่งเข้าระบบจริง)' })
  }

  async function updateBookingState(id, action) {
    setMessage(null)
    try {
      await api.post(`/bookings/${id}/${action}`, null, { params: { user_id: userId } })
      // คืนรถสำเร็จ → เด้ง popup ให้คะแนนจักรยานคันนั้นทันที
      const returned = myBookings.find((b) => b.id === id)
      await load()
      if (action === 'return' && returned) {
        setReviewFor(returned)
        setReviewRating(5)
        setReviewComment('')
      }
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    }
  }

  // ส่งรีวิวจาก popup หลังคืนรถ
  async function handleReviewSubmit(e) {
    e.preventDefault()
    if (!reviewFor) return
    setReviewSaving(true)
    try {
      await api.post('/reviews', {
        user_id: userId,
        bicycle_id: reviewFor.bicycle_id,
        rating: reviewRating,
        comment: reviewComment.trim(),
      })
      setReviewFor(null)
      setMessage({ type: 'success', text: 'ขอบคุณสำหรับคะแนนและความคิดเห็น!' })
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setReviewSaving(false)
    }
  }

  // เปิดฟอร์มแจ้งซ่อมแบบผูกจักรยานจากการจองคันนั้น
  function openReport(booking) {
    setReportFor(booking)
    setReportIssue('')
    setReportDesc('')
  }

  async function handleReportSubmit(e) {
    e.preventDefault()
    if (!reportFor) return
    setReportSaving(true)
    try {
      await api.post('/maintenance-reports', {
        bicycle_id: reportFor.bicycle_id,
        reported_by: userId,
        issue_type: reportIssue.trim(),
        description: reportDesc.trim(),
      })
      setReportFor(null)
      setMessage({ type: 'success', text: 'ส่งแจ้งปัญหาเรียบร้อย — ทีมช่างจะตรวจสอบให้' })
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setReportSaving(false)
    }
  }

  async function handleClearHistory() {
    if (!window.confirm('ล้างประวัติการจองที่จบไปแล้วทั้งหมด?\n(รายการที่ยังกำลังใช้งานอยู่จะไม่ถูกลบ)')) return
    setMessage(null)
    setClearing(true)
    try {
      const res = await api.delete('/bookings/history', { params: { user_id: userId } })
      setMessage({
        type: 'success',
        text: res.data.removed > 0
          ? `ล้างประวัติแล้ว ${res.data.removed} รายการ`
          : 'ไม่มีประวัติเก่าให้ล้าง',
      })
      await load()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setClearing(false)
    }
  }

  async function handleCreate(e) {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    setTimeError(null)
    // เวลาเริ่มรับรถ: "รับทันที" = ตอนนี้ / "เลือกเวลาอื่น" = เวลาที่ผู้ใช้กรอก (ต้องเป็นอนาคต)
    const start = new Date()
    if (pickupTime === 'later') {
      if (!laterTime) {
        setTimeError('กรุณาเลือกเวลาที่ต้องการรับรถ')
        setSaving(false)
        return
      }
      const [h, m] = laterTime.split(':').map(Number)
      start.setHours(h, m, 0, 0)
      if (start.getTime() <= Date.now()) {
        setTimeError('เวลาที่เลือกผ่านไปแล้ว — กรุณาเลือกเวลาในอนาคต')
        setSaving(false)
        return
      }
    }
    try {
      const end = new Date(start.getTime() + Number(duration) * 60 * 1000)
      await api.post('/bookings', {
        user_id: userId,
        bicycle_id: selectedBike.id,
        booking_type: pickupTime === 'now' ? 'walk_in' : 'advance_reservation',
        start_time: toIso(start),
        end_time: toIso(end),
        pickup_location: selectedBike.station,
        return_location: selectedBike.station,
        note: note || null,
      })
      setSelectedBike({ ...selectedBike, code: `BK-${Math.floor(1000 + Math.random() * 9000)}` })
      load()
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setSaving(false)
    }
  }

  if (selectedBike?.code?.startsWith('BK-')) {
    return <SuccessView bike={selectedBike} onBack={() => setSelectedBike(null)} />
  }

  if (!usersLoading && !currentUser) {
    return <p className="empty">กรุณาเข้าสู่ระบบด้วย Google ก่อนใช้งาน</p>
  }

  return (
    <div className="booking-page">
      <div className="booking-heading">
        <h1>เลือกจักรยานที่ต้องการ</h1>
        <p>เลือกคันที่ว่างใกล้คุณ แล้วยืนยันการจองได้ทันที</p>
        {/* mock: กรองรายการโปรด — modules/akeapon (ยังไม่เชื่อม backend) */}
        <FavoritesFilter count={favorites.length} checked={favOnly} onChange={setFavOnly} />
      </div>
      {message && <div className={`alert ${message.type === 'error' ? 'alert-error' : 'alert-success'}`}>{message.text}</div>}
      {/* เตือนใกล้ถึงเวลารับรถ (ภายใน 15 นาที) */}
      {pickupReminder && (
        <div className="alert alert-warn pickup-reminder">
          <span aria-hidden="true">⏰</span>
          <span>
            <strong>ใกล้ถึงเวลาไปรับรถแล้ว</strong> — {getBikeName(pickupReminder.bicycle_id)} เวลา {formatDateTime(pickupReminder.start_time)} ที่ {pickupReminder.pickup_location || 'จุดรับรถ'}
          </span>
          <button type="button" className="alert-close" onClick={() => setPickupReminder(null)} aria-label="ปิด">×</button>
        </div>
      )}
      {loading ? <p className="empty">กำลังโหลดข้อมูล...</p> : (
        <div className="bike-grid">
          {(favOnly ? bikes.filter((b) => favorites.includes(b.id)) : bikes).map((bike) => {
            const available = bike.available
            return <article className={`bike-card ${available ? '' : 'disabled'}`} key={bike.id}>
              <div className="bike-thumb" style={{ background: bike.tint }}>
                {bike.type === 'ไฟฟ้า' && <span className="bike-tag">ไฟฟ้า</span>}
                {/* mock: ปุ่มรายการโปรด — modules/akeapon (ยังไม่เชื่อม backend) */}
                <FavoriteButton active={favorites.includes(bike.id)} onToggle={() => toggleFavorite(bike.id)} />
                <BikeIcon />
              </div>
              <div className="bike-body">
                <h2>{bike.model}</h2>
                <p>{bike.station} · {bike.distance}</p>
                <div className="bike-meta">
                  <span>{bike.battery ? `แบตเตอรี่ ${bike.battery}%` : 'ไม่ใช้แบตเตอรี่'}</span>
                  <span className={`status-pill ${available ? 'free' : 'busy'}`}>{available ? 'ว่าง' : 'ไม่ว่าง'}</span>
                </div>
                <button className="select-btn" disabled={!available} onClick={() => setSelectedBike(bike)}>{available ? 'เลือกคันนี้' : 'มีผู้ใช้งานอยู่'}</button>
              </div>
            </article>
          })}
        </div>
      )}
      {favOnly && favorites.length === 0 && !loading && <p className="empty">ยังไม่มีรายการโปรด — กด ♡ ที่การ์ดจักรยานเพื่อเพิ่ม</p>}
      <section className="my-bookings">
        <div className="booking-heading">
          <div>
            <h2>{scope === 'all' ? 'การจองทั้งระบบ' : 'การจองของฉัน'}</h2>
            <p>
              {scope === 'all'
                ? 'มุมมองแอดมิน — การจองของผู้ใช้ทุกคนในระบบ'
                : 'ติดตามสถานะและจัดการการยืมจักรยาน'}
            </p>
          </div>
          <div className="section-head-actions">
            {isAdmin && (
              <div className="tabs">
                <button className={`tab ${scope === 'mine' ? 'active' : ''}`} onClick={() => switchScope('mine')}>
                  ของฉัน
                </button>
                <button className={`tab ${scope === 'all' ? 'active' : ''}`} onClick={() => switchScope('all')}>
                  ทั้งระบบ
                </button>
              </div>
            )}
            {scope === 'mine' && (
              <button
                className="btn btn-sm btn-ghost"
                onClick={handleClearHistory}
                disabled={clearing}
                title="ลบเฉพาะรายการที่จบไปแล้ว (เสร็จ/ยกเลิก/ไม่มา)"
              >
                {clearing ? 'กำลังล้าง...' : 'ล้างประวัติ'}
              </button>
            )}
          </div>
        </div>
        {myBookings.length === 0 ? <p className="empty">ยังไม่มีการจอง</p> : myBookings.map((booking) => {
          const isMine = Number(booking.user_id) === Number(userId)
          return (
            <article className="my-booking" key={booking.id}>
              <div>
                <strong>{getBikeName(booking.bicycle_id)}</strong>
                {scope === 'all' && <span>ผู้จอง: {getUserName(booking.user_id)}</span>}
                <span>{formatDateTime(booking.start_time)} - {formatDateTime(booking.end_time)}</span>
                {booking.note && <span className="booking-note">หมายเหตุ: {booking.note}</span>}
              </div>
              <span className={`status-pill ${booking.status === 'completed' ? 'free' : 'busy'}`}>
                {(BOOKING_STATUSES[booking.status] || {}).label || booking.status}
              </span>
              {/* ปุ่มจัดการ: เฉพาะ booking ของตัวเอง (แอดมินดูของคนอื่นได้แต่ไม่กดแทน) */}
              {isMine && (
                <div className="booking-actions">
                  {['pending', 'confirmed'].includes(booking.status) && <><button className="btn btn-primary btn-sm" onClick={() => updateBookingState(booking.id, 'borrow')}>รับรถ</button><button className="btn btn-ghost btn-sm" onClick={() => updateBookingState(booking.id, 'cancel')}>ยกเลิก</button></>}
                  {booking.status === 'in_progress' && <button className="btn btn-primary btn-sm" onClick={() => updateBookingState(booking.id, 'return')}>คืนรถ</button>}
                  {/* แจ้งปัญหา — ใช้ได้ตั้งแต่รับรถแล้ว (in_progress) จนถึงหลังคืนรถ (completed) */}
                  {['in_progress', 'completed'].includes(booking.status) && <button className="btn btn-ghost btn-sm" onClick={() => openReport(booking)}>แจ้งปัญหา</button>}
                  {/* แจ้งของหาย — modules/akeapon (mock localStorage ยังไม่เชื่อม backend) */}
                  {['in_progress', 'completed'].includes(booking.status) && <button className="btn btn-ghost btn-sm" onClick={() => openLost(booking)}>แจ้งของหาย</button>}
                </div>
              )}
            </article>
          )
        })}
      </section>
      {/* mock: ประวัติการแจ้งของหาย — modules/akeapon (localStorage ยังไม่เชื่อม backend) */}
      <LostItemHistory items={lostItems} getBikeName={getBikeName} />
      {lostFor && (
        <LostItemModal
          booking={lostFor}
          bikeName={getBikeName(lostFor.bicycle_id)}
          onClose={closeLost}
          onSubmit={handleLostSaved}
        />
      )}
      {selectedBike && <form className="booking-modal" onSubmit={handleCreate}>
        <div className="modal-card">
          <button type="button" className="modal-close" onClick={() => setSelectedBike(null)} aria-label="ปิด">×</button>
          <div className="summary-row"><BikeIcon /><div><strong>{selectedBike.model} · {selectedBike.code}</strong><span>{selectedBike.station} · ห่างจากคุณ {selectedBike.distance}</span></div></div>
          <div className="field"><label htmlFor="pickup-time">เวลารับรถ</label><select id="pickup-time" value={pickupTime} onChange={(e) => { setPickupTime(e.target.value); setTimeError(null); if (e.target.value === 'later' && !laterTime) setLaterTime(defaultLaterTime()) }}><option value="now">รับทันที</option><option value="later">เลือกเวลาอื่น</option></select></div>
          {pickupTime === 'later' && (
            <div className="field">
              <label>เวลามารับรถ * (รูปแบบ 24 ชั่วโมง)</label>
              <Time24 value={laterTime} onChange={(v) => { setLaterTime(v); setTimeError(null) }} />
              <small>ระบบจะเตือนคุณประมาณ 15 นาทีก่อนถึงเวลารับรถ</small>
              {timeError && <small className="field-error">{timeError}</small>}
            </div>
          )}
          <div className="field"><label htmlFor="duration">ระยะเวลาที่ต้องการยืม</label><select id="duration" value={duration} onChange={(e) => setDuration(e.target.value)}><option value="30">30 นาที</option><option value="60">1 ชั่วโมง</option><option value="120">2 ชั่วโมง</option><option value="480">ทั้งวัน</option></select></div>
          <div className="field"><label htmlFor="note">หมายเหตุ (ถ้ามี)</label><textarea id="note" value={note} onChange={(e) => setNote(e.target.value)} placeholder="เช่น จุดสังเกตเพิ่มเติม หรือคำขอพิเศษ" /><small>ไม่บังคับกรอก</small></div>
          <div className="confirm-actions"><button className="btn btn-primary" disabled={saving}>{saving ? 'กำลังบันทึก...' : 'ยืนยันการจอง'}</button><button type="button" className="btn btn-ghost" onClick={() => setSelectedBike(null)}>ยกเลิก</button></div>
        </div>
      </form>}
      {reviewFor && (
        <form className="booking-modal" onSubmit={handleReviewSubmit}>
          <div className="modal-card">
            <button type="button" className="modal-close" onClick={() => setReviewFor(null)} aria-label="ปิด">×</button>
            <div className="summary-row"><BikeIcon /><div><strong>คืนรถสำเร็จ!</strong><span>{getBikeName(reviewFor.bicycle_id)} · ช่วยให้คะแนนหน่อยนะ</span></div></div>
            <div className="field">
              <label>คะแนน (กดครึ่งซ้ายของดาว = ครึ่งดาว) *</label>
              <Stars value={reviewRating} allowHalf onPick={setReviewRating} />
              <small>คะแนนปัจจุบัน: {reviewRating.toFixed(1)} / 5.0</small>
            </div>
            <div className="field">
              <label htmlFor="review-comment">ความคิดเห็น *</label>
              <textarea
                id="review-comment"
                value={reviewComment}
                onChange={(e) => setReviewComment(e.target.value)}
                placeholder="เช่น ขี่ลื่นดี แต่เบาะปรับยากนิดหน่อย"
                required
              />
            </div>
            <div className="confirm-actions">
              <button className="btn btn-primary" disabled={reviewSaving || !reviewComment.trim()}>
                {reviewSaving ? 'กำลังบันทึก...' : 'ส่งคะแนน'}
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => setReviewFor(null)}>ข้าม</button>
            </div>
          </div>
        </form>
      )}
      {reportFor && (
        <form className="booking-modal" onSubmit={handleReportSubmit}>
          <div className="modal-card">
            <button type="button" className="modal-close" onClick={() => setReportFor(null)} aria-label="ปิด">×</button>
            <div className="summary-row"><BikeIcon /><div><strong>แจ้งปัญหาจักรยาน</strong><span>{getBikeName(reportFor.bicycle_id)} · จักรยาน #{reportFor.bicycle_id}</span></div></div>
            <div className="field">
              <label htmlFor="report-issue">ประเภทปัญหา *</label>
              <input
                id="report-issue"
                list="report-issue-options"
                maxLength={50}
                value={reportIssue}
                onChange={(e) => setReportIssue(e.target.value)}
                placeholder="เช่น ยางแบน เบรกหลวม โซ่หลุด"
                required
              />
              <datalist id="report-issue-options">
                <option value="ยางแบน" />
                <option value="เบรกหลวม" />
                <option value="โซ่หลุด" />
                <option value="ล้อเอียง" />
                <option value="ไฟหน้าดับ" />
              </datalist>
            </div>
            <div className="field">
              <label htmlFor="report-desc">รายละเอียด *</label>
              <textarea
                id="report-desc"
                value={reportDesc}
                onChange={(e) => setReportDesc(e.target.value)}
                placeholder="อธิบายสิ่งที่เจอเพิ่มเติม"
                required
              />
            </div>
            <div className="confirm-actions">
              <button className="btn btn-primary" disabled={reportSaving || !reportIssue.trim() || !reportDesc.trim()}>
                {reportSaving ? 'กำลังส่ง...' : 'ส่งแจ้งปัญหา'}
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => setReportFor(null)}>ยกเลิก</button>
            </div>
          </div>
        </form>
      )}
    </div>
  )
}

function SuccessView({ bike, onBack }) {
  return <div className="success-view"><div className="success-icon">✓</div><h1>จองสำเร็จ</h1><p>ไปที่ {bike.station} แล้วยื่นบัตรประชาชนหรือบัตรนักศึกษาเพื่อเข้าใช้งานจักรยาน {bike.model} {bike.id}</p><div className="qr-box" /><div className="booking-code">{bike.code}</div><button className="btn btn-primary" onClick={onBack}>กลับไปหน้าเลือกจักรยาน</button></div>
}