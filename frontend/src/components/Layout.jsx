import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useCurrentUser } from '../context/currentUser'
import { formatDateTime } from '../utils'
import { api } from '../api'

const navItems = [
  { to: '/', label: '🏠 หน้าหลัก' },
  { to: '/bookings', label: 'การจองจักรยาน' },
  { to: '/group-rides', label: 'กลุ่มปั่นร่วมกัน' },
  { to: '/support', label: 'แจ้งปัญหา' },
  { to: '/maintenance', label: 'แจ้งซ่อม' },
  { to: '/reviews', label: 'รีวิว & คะแนน' },
  { to: '/notifications', label: 'การแจ้งเตือน' },
  { to: '/scores', label: 'คะแนน & บทลงโทษ' },
  { to: '/favorites', label: 'รายการโปรด' },
  { to: '/lost-items', label: 'ของหาย' },
]

const adminNavItems = [
  { to: '/admin', label: '🛡️ จัดการผู้ใช้' },
]

export default function Layout() {
  const { currentUser, isAdmin, notifications, unreadCount, refreshNotifications, markNotificationRead, clearReadNotifications } = useCurrentUser()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [bellOpen, setBellOpen] = useState(false)
  const bellRef = useRef(null)

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
          <div className="brand">
            <span className="brand-mark" aria-hidden="true">⌁</span>
            <span className="brand-text">BikeShare</span>
          </div>
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
          <div className="welcome">
            ยินดีต้อนรับ<br /><strong>{displayName}</strong><br />
            <span className={`badge ${isAdmin ? 'badge-admin' : 'badge-user'}`}>
              {isAdmin ? 'แอดมิน — เห็นทุกอย่าง' : 'ผู้ใช้ทั่วไป'}
            </span>
          </div>
          <nav className="sidebar-nav">
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}>
                {item.label}
              </NavLink>
            ))}
            {isAdmin && (
              <>
                <div className="sidebar-nav-divider"><span>แอดมิน</span></div>
                {adminNavItems.map((item) => (
                  <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? 'nav-item nav-item-admin active' : 'nav-item nav-item-admin')}>
                    {item.label}
                  </NavLink>
                ))}
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
