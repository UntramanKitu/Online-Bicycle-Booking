import { Link } from 'react-router-dom'
import { useCurrentUser } from '../context/currentUser'
import './home.css'

// ศูนย์รวมทางเข้าทุกฟีเจอร์ (sidebar เหลือแค่ จอง/ปั่นกลุ่ม — ที่เหลือเข้าจากหน้านี้)
const SECTIONS = [
  {
    title: 'เช่า & ปั่น',
    owner: 'ชัยอนันต์',
    items: [
      { to: '/bookings', icon: '🚲', label: 'การจองจักรยาน', desc: 'จอง–คืนรถ เลือกเวลาและสถานี' },
      { to: '/group-rides', icon: '👥', label: 'กลุ่มปั่นร่วมกัน', desc: 'นัดปั่นรวมตัวกันเป็นกลุ่ม' },
    ],
  },
  {
    title: 'ดูแลรถ',
    owner: 'นาธิดา',
    items: [
      { to: '/maintenance', icon: '🔧', label: 'แจ้งซ่อม', desc: 'รายงานรถเสีย ติดตามสถานะซ่อม' },
      { to: '/reviews', icon: '⭐', label: 'รีวิว & คะแนน', desc: 'ให้คะแนนหลังใช้งานแต่ละครั้ง' },
      { to: '/notifications', icon: '🔔', label: 'การแจ้งเตือน', desc: 'ดูแจ้งเตือนทั้งหมดย้อนหลัง' },
    ],
  },
  {
    title: 'คะแนน & ของหาย',
    owner: 'เอกพล',
    items: [
      { to: '/scores', icon: '🏆', label: 'คะแนน & บทลงโทษ', desc: 'แต้มพฤติกรรมและประวัติลงโทษ' },
      { to: '/favorites', icon: '♥', label: 'รายการโปรด', desc: 'จักรยานคู่ใจที่กดไว้' },
      { to: '/lost-items', icon: '🎒', label: 'ของหาย', desc: 'ดูของหายทั้งระบบ · แจ้งของตัวเองที่โปรไฟล์' },
    ],
  },
  {
    title: 'ช่วยเหลือ',
    owner: 'ระบบ',
    items: [
      { to: '/support', icon: '🎫', label: 'แจ้งปัญหา', desc: 'ส่งคำร้อง/ปัญหาการใช้งานทั่วไป' },
    ],
  },
]

export default function HomePage() {
  const { currentUser, isAdmin } = useCurrentUser()
  const name = currentUser?.full_name || currentUser?.username || 'ผู้ใช้'

  return (
    <div className="page-section home-page">
      <section className="home-hero">
        <div>
          <h1 className="section-title">สวัสดี, {name} 👋</h1>
          <p className="section-subtitle">
            ศูนย์กลางระบบ BikeShare — เลือกเมนูด้านล่างเพื่อใช้งานได้ทันที
          </p>
        </div>
        <div className="home-hero-stats">
          <span className={`badge ${isAdmin ? 'badge-admin' : 'badge-user'}`}>
            {isAdmin ? 'แอดมิน' : 'ผู้ใช้ทั่วไป'}
          </span>
          {typeof currentUser?.points === 'number' && (
            <span className="home-points">⭐ {currentUser.points} คะแนน</span>
          )}
        </div>
      </section>

      {SECTIONS.map((section) => (
        <section key={section.title} className="home-section">
          <div className="home-section-head">
            <h2>{section.title}</h2>
            <span className="home-owner">โมดูล: {section.owner}</span>
          </div>
          <div className="home-grid">
            {section.items.map((item) => (
              <Link key={item.to} to={item.to} className="home-card">
                <span className="home-card-icon" aria-hidden="true">{item.icon}</span>
                <span className="home-card-body">
                  <strong>{item.label}</strong>
                  <span className="muted small">{item.desc}</span>
                </span>
                <span className="home-card-arrow" aria-hidden="true">›</span>
              </Link>
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}
