import { formatDateTime } from '../../../utils'

// mock: ประวัติการแจ้งของหาย (localStorage) — ยังไม่เชื่อม backend
export default function LostItemHistory({ items, getBikeName }) {
  if (!items || items.length === 0) return null
  return (
    <section className="my-bookings">
      <div className="booking-heading">
        <div>
          <h2>การแจ้งของหายของฉัน</h2>
          <p>ข้อมูลจำลอง (mock) — ยังไม่เชื่อมเซิร์ฟเวอร์</p>
        </div>
      </div>
      {items.map((it) => (
        <article className="my-booking" key={it.id}>
          <div>
            <strong>{it.item_name}</strong>
            <span>การจอง #{it.booking_id} · {getBikeName(it.bicycle_id)} · {it.location || 'ไม่ระบุสถานที่'}</span>
            {it.description && <span className="booking-note">รายละเอียด: {it.description}</span>}
            <span>แจ้งเมื่อ {formatDateTime(it.created_at)}</span>
          </div>
          <span className="status-pill busy">{it.status}</span>
        </article>
      ))}
    </section>
  )
}