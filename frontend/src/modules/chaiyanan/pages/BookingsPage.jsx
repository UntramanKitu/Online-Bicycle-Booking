import { useEffect, useState } from 'react'
import { api, getApiError } from '../../../api'
import { toIso } from '../../../utils'
import { useCurrentUser } from '../../../context/CurrentUserContext'

function BikeIcon() {
  return <svg className="bike-illustration" width="64" height="40" viewBox="0 0 64 40" fill="none" aria-hidden="true">
    <circle cx="12" cy="30" r="8" />
    <circle cx="50" cy="30" r="8" />
    <path d="M12 30 24 12h12L26 30M32 12l18 18M20 12h14M24 12l-4-6" />
  </svg>
}

export default function BookingsPage() {
  const { userId } = useCurrentUser()
  const [bikes, setBikes] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedBike, setSelectedBike] = useState(null)
  const [duration, setDuration] = useState('30')
  const [pickupTime, setPickupTime] = useState('now')
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)

  async function load() {
    setLoading(true)
    try {
      const bicycleRes = await api.get('/bicycles')
      setBikes(bicycleRes.data)
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(load, 0)
    return () => window.clearTimeout(timer)
  }, [])

  async function handleCreate(e) {
    e.preventDefault()
    setSaving(true)
    setMessage(null)
    try {
      const start = new Date()
      const end = new Date(start.getTime() + Number(duration) * 60 * 1000)
      await api.post('/bookings', {
        user_id: userId,
        bicycle_id: selectedBike.id,
        booking_type: pickupTime === 'now' ? 'walk_in' : 'advance_reservation',
        start_time: toIso(start),
        end_time: toIso(end),
        pickup_location: selectedBike.station,
        return_location: note || null,
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

  return (
    <div className="booking-page">
      <div className="booking-heading">
        <h1>เลือกจักรยานที่ต้องการ</h1>
        <p>เลือกคันที่ว่างใกล้คุณ แล้วยืนยันการจองได้ทันที</p>
      </div>
      {message && <div className="alert alert-error">{message.text}</div>}
      {loading ? <p className="empty">กำลังโหลดข้อมูล...</p> : (
        <div className="bike-grid">
          {bikes.map((bike) => {
            const available = bike.available
            return <article className={`bike-card ${available ? '' : 'disabled'}`} key={bike.id}>
              <div className="bike-thumb" style={{ background: bike.tint }}>
                {bike.type === 'ไฟฟ้า' && <span className="bike-tag">ไฟฟ้า</span>}
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
      {selectedBike && <form className="booking-modal" onSubmit={handleCreate}>
        <div className="modal-card">
          <button type="button" className="modal-close" onClick={() => setSelectedBike(null)} aria-label="ปิด">×</button>
          <div className="summary-row"><BikeIcon /><div><strong>{selectedBike.model} · {selectedBike.code}</strong><span>{selectedBike.station} · ห่างจากคุณ {selectedBike.distance}</span></div></div>
          <div className="field"><label htmlFor="pickup-time">เวลารับรถ</label><select id="pickup-time" value={pickupTime} onChange={(e) => setPickupTime(e.target.value)}><option value="now">รับทันที</option><option value="later">เลือกเวลาอื่น</option></select></div>
          <div className="field"><label htmlFor="duration">ระยะเวลาที่ต้องการยืม</label><select id="duration" value={duration} onChange={(e) => setDuration(e.target.value)}><option value="30">30 นาที</option><option value="60">1 ชั่วโมง</option><option value="120">2 ชั่วโมง</option><option value="480">ทั้งวัน</option></select></div>
          <div className="field"><label htmlFor="note">หมายเหตุ (ถ้ามี)</label><textarea id="note" value={note} onChange={(e) => setNote(e.target.value)} placeholder="เช่น จุดสังเกตเพิ่มเติม หรือคำขอพิเศษ" /><small>ไม่บังคับกรอก</small></div>
          <div className="confirm-actions"><button className="btn btn-primary" disabled={saving}>{saving ? 'กำลังบันทึก...' : 'ยืนยันการจอง'}</button><button type="button" className="btn btn-ghost" onClick={() => setSelectedBike(null)}>ยกเลิก</button></div>
        </div>
      </form>}
    </div>
  )
}

function SuccessView({ bike, onBack }) {
  return <div className="success-view"><div className="success-icon">✓</div><h1>จองสำเร็จ</h1><p>ไปที่ {bike.station} แล้วสแกนรหัสด้านล่างที่ตัวล็อกจักรยานเพื่อปลดล็อก {bike.model} ({bike.id})</p><div className="qr-box" /><div className="booking-code">{bike.code}</div><button className="btn btn-primary" onClick={onBack}>กลับไปหน้าเลือกจักรยาน</button></div>
}