import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useCurrentUser } from '../context/CurrentUserContext'

const navItems = [
  { to: '/bookings', label: 'จองจักรยาน' },
  { to: '/group-rides', label: 'กลุ่มปั่นร่วมกัน' },
  { to: '/support', label: 'แจ้งปัญหา' },
]

export default function Layout() {
  const { userId, setUserId } = useCurrentUser()
  const [sidebarOpen, setSidebarOpen] = useState(true)

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
            <span className="notification" aria-label="การแจ้งเตือน">♧</span>
            <label htmlFor="currentUser">สมชาย ใจดี</label>
            <input
              id="currentUser"
              type="number"
              min="1"
              value={userId}
              onChange={(e) => setUserId(Number(e.target.value) || 1)}
            />
            <button className="logout-button" type="button">ออกจากระบบ</button>
          </div>
        </div>
      </header>

      <div className="reference-layout">
        <aside className={`reference-sidebar ${sidebarOpen ? '' : 'hidden'}`}>
          <div className="welcome">ยินดีต้อนรับ<br /><strong>สมชาย ใจดี</strong></div>
          <nav className="sidebar-nav">
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}>
                {item.label}
              </NavLink>
            ))}
            <a className="nav-item" href="#">จักรยาน/สถานีโปรด</a>
            <a className="nav-item" href="#">การแจ้งเตือน</a>
          </nav>
        </aside>

        <main className="page"><Outlet /></main>
      </div>

      <footer className="app-footer">ระบบจองยืมจักรยานออนไลน์ · BikeShare</footer>
    </div>
  )
}