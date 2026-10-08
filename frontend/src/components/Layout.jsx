import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useCurrentUser } from '../context/currentUser'
import { formatDateTime } from '../utils'
import { api } from '../api'

const navItems = [
  { to: '/', label: '🏠 หน้าหลัก' },
  { to: '/bookings', label: '🚲 จอง' },
  { to: '/group-rides', label: '👥 ปั่นกลุ่ม' },
  // ของหาย = หน้าระบบ (ทุกคนเห็นของทั้งหมด) — ของตัวเองดู/แจ้งที่แท็บ 🎒 ในโปรไฟล์
  { to: '/lost-items', label: '🎒 ของหาย' },
]

const adminNavItems = [
  { to: '/admin', label: '🛡️ จัดการผู้ใช้', end: true },
  { to: '/admin/bikes', label: '🚲 จัดการจักรยาน', end: true },
  { to: '/support?scope=all', label: '🎫 จัดการปัญหา', end: true },
  { to: '/maintenance?scope=all', label: '🔧 จัดการซ่อม', end: true },
]

// เมนูฝั่ง sidebar ที่ใช้แทนเมนูหลักเมื่อผู้ใช้อยู่ที่ /profile (tab ผูกกับ ?tab=)
// = ศูนย์รวมฟีเจอร์ที่ต้องใช้ทั้งหมดของโปรไฟล์ ป้ายสั้น อ่านง่าย
const profileNavItems = [
  { tab: 'info', label: '👤 ข้อมูลของฉัน' },
  { tab: 'edit', label: '✏️ แก้ไขชื่อ' },
  { tab: 'tickets', label: '🎫 แจ้งปัญหา' },
  { tab: 'favorites', label: '♥ รายการโปรด' },
  { tab: 'maintenance', label: '🔧 แจ้งซ่อม' },
  { tab: 'reviews', label: '⭐ รีวิว' },
  { tab: 'scores', label: '🏆 คะแนน' },
  { tab: 'lost', label: '🎒 ของหาย' },
]



export default function Layout() {
  const { currentUser, isAdmin, notifications, unreadCount, refreshNotifications, markNotificationRead, clearReadNotifications } = useCurrentUser()
  const navigate = useNavigate()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [bellOpen, setBellOpen] = useState(false)
  const bellRef = useRef(null)

  // อยู่หน้าโปรไฟล์ → sidebar แสดงเมนูโปรไฟล์แทนเมนูหลัก (tab ปัจจุบันอ่านจาก ?tab=)
  const isProfilePage = location.pathname === '/profile'
  const activeProfileTab = new URLSearchParams(location.search).get('tab') || 'info'
  // อยู่ในโซนหน้าจัดการ (/admin, จัดการปัญหา/ซ่อม ของแอดมิน) → sidebar แสดงเมนูแอดมิน
  const isAdminSection = isAdmin && (
    location.pathname.startsWith('/admin')
    || location.pathname === '/support'
    || location.pathname === '/maintenance'
  )

  const displayName = currentUser?.full_name || currentUser?.username || 'ผู้ใช้'
  const readCount = Math.max(0, notifications.length - unreadCount)

  // กดข้างนอกให้ dropdown กระดิ่งปิด
  useEffect(() => {
    if (!bellOpen) return
    const onClick = (e) => {
      if (bellRef.current && !bellRef.current.contains(e.target)) setBellOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [bellOpen])

  return (
    <div className="app reference-shell">
      <header className="app-header reference-header">
        <div className="app-header-inner">
          <button className="menu-button" type="button" aria-label="เปิดเมนู" onClick={() => setSidebarOpen((open) => !open)}>
            <span />
          </button>
            <Link className="brand brand-link" to="/" aria-label="กลับหน้าหลัก">
              <span className="brand-mark" aria-hidden="true">⌁</span>
              <span className="brand-text">BikeShare</span>
            </Link>
          <div className="user-picker reference-user">
            <div className="bell-wrap" ref={bellRef}>
              <button
                className="bell-button"
                type="button"
                aria-label={`การแจ้งเตือน (${unreadCount} ยังไม่ได้อ่าน)`}
                aria-expanded={bellOpen}
                onClick={() => { setBellOpen((v) => !v); if (!bellOpen) refreshNotifications() }}
              >
                🔔
                {unreadCount > 0 && <span className="bell-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>}
              </button>
              {bellOpen && (
                <div className="bell-dropdown" role="menu">
                  <div className="bell-dropdown-head">
                    <strong>การแจ้งเตือน</strong>
                    <span className="bell-count">ใหม่ {unreadCount} · ทั้งหมด {notifications.length}</span>
                  </div>
                  <div className="bell-dropdown-actions">
                    {readCount > 0 && (
                      <button className="btn btn-sm btn-ghost" type="button" onClick={() => clearReadNotifications()}>
                        ล้างที่อ่านแล้ว ({readCount})
                      </button>
                    )}
                    <button className="btn btn-sm btn-ghost" type="button" onClick={() => { setBellOpen(false); navigate('/notifications') }}>
                      ดูทั้งหมด
                    </button>
                  </div>
                  {notifications.length === 0 ? (
                    <p className="empty small">ยังไม่มีการแจ้งเตือน</p>
                  ) : (
                    notifications.slice(0, 8).map((n) => (
                      <button
                        key={n.id}
                        type="button"
                        className={`bell-item ${n.is_read ? '' : 'unread'}`}
                        onClick={() => markNotificationRead(n.id)}
                      >
                        <span className="bell-item-title">{n.title}</span>
                        <span className="bell-item-msg">{n.message}</span>
                        <span className="muted small">{formatDateTime(n.created_at)}</span>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>
            <span className="current-user-name">{displayName}</span>
            <span className={`badge ${isAdmin ? 'badge-admin' : 'badge-user'}`}>
              {isAdmin ? 'แอดมิน' : 'ผู้ใช้ทั่วไป'}
            </span>
            <button className="logout-button" type="button" onClick={async () => { await api.post('/auth/logout'); navigate('/login') }}>ออกจากระบบ</button>
          </div>
        </div>
      </header>

      <div className="reference-layout">
        <aside className={`reference-sidebar ${sidebarOpen ? '' : 'hidden'}`}>
          <Link className="welcome welcome-link" to="/profile" title="เปิดโปรไฟล์ของฉัน">
            ยินดีต้อนรับ<br /><strong>{displayName}</strong><br />
            <span className={`badge ${isAdmin ? 'badge-admin' : 'badge-user'}`}>
              {isAdmin ? 'แอดมิน — เห็นทุกอย่าง' : 'ผู้ใช้ทั่วไป'}
            </span>
            <span className="welcome-hint">เปิดโปรไฟล์ ›</span>
          </Link>
          <nav className="sidebar-nav">
            {isProfilePage ? (
              <>
                <div className="sidebar-nav-divider"><span>เมนูโปรไฟล์</span></div>
                {profileNavItems.map((item) => (
                  <Link
                    key={item.tab}
                    to={`/profile?tab=${item.tab}`}
                    className={`nav-item ${activeProfileTab === item.tab ? 'active' : ''}`}
                  >
                    {item.label}
                  </Link>
                ))}
                <div className="sidebar-nav-divider"><span>เมนูหลัก</span></div>
                <NavLink to="/" className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}>
                  🏠 กลับหน้าหลัก
                </NavLink>
              </>
            ) : isAdminSection ? (
              <>
                <div className="sidebar-nav-divider"><span>เมนูแอดมิน</span></div>
                {adminNavItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.end}
                    className={({ isActive }) => (isActive ? 'nav-item nav-item-admin active' : 'nav-item nav-item-admin')}
                  >
                    {item.label}
                  </NavLink>
                ))}
                <div className="sidebar-nav-divider"><span>เมนูอื่น</span></div>
                <NavLink to="/" className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}>
                  🏠 กลับหน้าหลัก
                </NavLink>
              </>
            ) : (
              <>
                {navItems.map((item) => (
                  <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}>
                    {item.label}
                  </NavLink>
                ))}
                {isAdmin && (
                  <>
                    <div className="sidebar-nav-divider"><span>แอดมิน</span></div>
                    <NavLink
                      to="/admin"
                      className={({ isActive }) => (isActive ? 'nav-item nav-item-admin active' : 'nav-item nav-item-admin')}
                    >
                      🛡️ หน้าแอดมิน
                    </NavLink>
                  </>
                )}
              </>
            )}
          </nav>
        </aside>

        <main className="page"><Outlet /></main>
      </div>

      <footer className="app-footer">ระบบจองยืม· BikeShare</footer>
    </div>
  )
}
