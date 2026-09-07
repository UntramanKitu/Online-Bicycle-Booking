import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useCurrentUser } from '../context/CurrentUserContext'
import { api } from '../api'

const navItems = [
  { to: '/bookings', label: 'การจองจักรยาน' },
  { to: '/group-rides', label: 'กลุ่มปั่นร่วมกัน' },
  { to: '/support', label: 'แจ้งปัญหา' },
]

export default function Layout() {
  const { userId, setUserId, users, currentUser } = useCurrentUser()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const displayName = currentUser ? currentUser.full_name : `ผู้ใช้ #${userId}`

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
            <span className="notification" aria-label="การแแจ้งเตือน">♧</span>
            <label htmlFor="currentUser">{displayName}</label>
            <select
              id="currentUser"
              value={userId}
              onChange={(e) => setUserId(Number(e.target.value))}
              aria-label="เปลี่ยน ผู้ใช้ปัจจุบัน"
            >
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name} ({u.role})
                </option>
              ))}
            </select>
            <button className="logout-button" type="button" onClick={async () => { await api.post('/auth/logout'); navigate('/login') }}>ออกจากระบบ</button>
          </div>
        </div>
      </header>

      <div className="reference-layout">
        <aside className={`reference-sidebar ${sidebarOpen ? '' : 'hidden'}`}>
          <div className="welcome">ยินดีต้อนรับ<br /><strong>{displayName}</strong></div>
          <nav className="sidebar-nav">
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}>
                {item.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <main className="page"><Outlet /></main>
      </div>

      <footer className="app-footer">ระบบจองยืม· BikeShare</footer>
    </div>
  )
}
