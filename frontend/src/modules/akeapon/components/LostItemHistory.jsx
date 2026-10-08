import { Link } from 'react-router-dom'
import { formatDateTime } from '../../../utils'

const STATUS_LABELS = {
  lost: '🔍 แจ้งหาย',
  found: '✅ เจอแล้ว',
}

// ประวัติการแจ้งของหายของฉัน — ข้อมูลจริงจาก backend (ชุดเดียวกับแท็บ 🎒 ของหายในโปรไฟล์)
export default function LostItemHistory({ items, getBikeName }) {
  const has = items && items.length > 0
  return (
    <section className="my-bookings">
      <div className="booking-heading">
        <div>
          <h2>การแจ้งของหายของฉัน</h2>
          <p>ข้อมูลจากทุกช่องทาง (รวมถึงแท็บ 🎒 ของหายในโปรไฟล์)</p>
        </div>
        <Link className="btn btn-sm btn-primary" to="/profile?tab=lost">ดู/จัดการที่โปรไฟล์</Link>
      </div>
      {!has ? (
        <p className="empty">ยังไม่มีการแจ้งของหาย — กดปุ่ม "แจ้งของหาย" ในการ์ดจองด้านบนได้เลย</p>
      ) : items.map((it) => (
        <article className="my-booking" key={it.id}>
          <div>
            <strong>{it.item_name}</strong>
            <span>{it.bicycle_id ? getBikeName(it.bicycle_id) : 'ไม่ระบุจักรยาน'} · {it.location || 'ไม่ระบุสถานที่'}</span>
            {it.description && <span className="booking-note">รายละเอียด: {it.description}</span>}
            <span>แจ้งเมื่อ {formatDateTime(it.created_at)}</span>
          </div>
          <span className={`status-pill ${it.status === 'found' ? 'free' : 'busy'}`}>
            {STATUS_LABELS[it.status] || it.status}
          </span>
        </article>
      ))}
    </section>
  )
}