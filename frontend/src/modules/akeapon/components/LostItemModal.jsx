import { useState } from 'react'

const EMPTY = { item_name: '', location: '', description: '' }

function BikeIcon() {
  return <svg className="bike-illustration" width="64" height="40" viewBox="0 0 64 40" fill="none" aria-hidden="true">
    <circle cx="12" cy="30" r="8" />
    <circle cx="50" cy="30" r="8" />
    <path d="M12 30 24 12h12L26 30M32 12l18 18M20 12h14M24 12l-4-6" />
  </svg>
}

// ฟอร์มแจ้งของหายจากหน้าการจอง — ส่งเข้า backend `/api/lost-items` จริง (รายการเดียวกับแท็บโปรไฟล์)
export default function LostItemModal({ booking, bikeName, onClose, onSubmit }) {
  const [form, setForm] = useState(EMPTY)

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit({
      bicycle_id: booking.bicycle_id,
      item_name: form.item_name.trim(),
      location: form.location.trim(),
      description: form.description.trim(),
    })
    // ไม่ล้างฟอร์มตรงนี้ — ถ้าบันทึกไม่สำเร็จ ผู้ใช้จะได้พิมพ์ต่อจากข้อมูลเดิม (สำเร็จ = หน้าปิดให้เอง)
  }

  return (
    <form className="booking-modal" onSubmit={handleSubmit}>
      <div className="modal-card">
        <button type="button" className="modal-close" onClick={onClose} aria-label="ปิด">×</button>
        <div className="summary-row"><BikeIcon /><div><strong>แจ้งของหาย</strong><span>{bikeName} · การจอง #{booking.id}</span></div></div>
        <div className="field"><label htmlFor="lost-item">สิ่งของที่หาย *</label><input id="lost-item" value={form.item_name} onChange={(e) => setForm({ ...form, item_name: e.target.value })} placeholder="เช่น ขวดน้ำ แจ็คเก็ต แว่นตา" required /></div>
        <div className="field"><label htmlFor="lost-loc">สถานที่ที่คาดว่าทำหาย</label><input id="lost-loc" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} placeholder="เช่น ตะกร้าหน้ารถ ห้องสมุด" /></div>
        <div className="field"><label htmlFor="lost-desc">รายละเอียดเพิ่มเติม</label><textarea id="lost-desc" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="สี ยี่ห้อ จุดสังเกต" /></div>
        <div className="confirm-actions">
          <button className="btn btn-primary">บันทึกการแจ้ง</button>
          <button type="button" className="btn btn-ghost" onClick={onClose}>ยกเลิก</button>
        </div>
      </div>
    </form>
  )
}