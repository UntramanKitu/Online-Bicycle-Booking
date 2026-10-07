import { useEffect, useState } from 'react'
import { api } from '../../api'
import { useCurrentUser } from '../../context/currentUser'

export default function AdminDashboard() {
  const { currentUser } = useCurrentUser()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [updating, setUpdating] = useState(null) // user_id กำลังอัพเดท
  const [search, setSearch] = useState('')
  const [filterRole, setFilterRole] = useState('all')

  const loadUsers = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.get('/admin/users')
      setUsers(res.data || [])
    } catch (e) {
      setError(e?.response?.data?.detail || 'โหลดข้อมูลไม่สำเร็จ')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // เลื่อนไป task ถัดไป — กันกฎ react-hooks/set-state-in-effect (setState ใน effect)
    const timer = window.setTimeout(() => loadUsers(), 0)
    return () => window.clearTimeout(timer)
  }, [])

  const handleToggleRole = async (user) => {
    const newRole = user.role === 'admin' ? 'user' : 'admin'
    setUpdating(user.id)
    try {
      const res = await api.patch(`/admin/users/${user.id}/role`, { role: newRole })
      setUsers((prev) => prev.map((u) => (u.id === res.data.id ? res.data : u)))
    } catch (e) {
      alert(e?.response?.data?.detail || 'อัพเดทไม่สำเร็จ')
    } finally {
      setUpdating(null)
    }
  }

  const filtered = users.filter((u) => {
    const matchSearch =
      !search ||
      u.full_name?.toLowerCase().includes(search.toLowerCase()) ||
      u.username?.toLowerCase().includes(search.toLowerCase()) ||
      u.email?.toLowerCase().includes(search.toLowerCase())
    const matchRole = filterRole === 'all' || u.role === filterRole
    return matchSearch && matchRole
  })

  const adminCount = users.filter((u) => u.role === 'admin').length
  const userCount = users.filter((u) => u.role === 'user').length

  return (
    <div className="admin-dashboard">
      {/* Header */}
      <div className="admin-header">
        <div>
          <h1 className="admin-title">
            <span className="admin-title-icon">🛡️</span>
            จัดการผู้ใช้ (Admin Dashboard)
          </h1>
          <p className="admin-subtitle">
            เห็นและจัดการข้อมูลผู้ใช้ทุกคนในระบบ — ล็อกอินเป็น <strong>{currentUser?.full_name || currentUser?.username}</strong>
          </p>
        </div>
        <button
          id="admin-refresh-btn"
          className="btn btn-ghost"
          onClick={loadUsers}
          disabled={loading}
          title="รีเฟรชข้อมูล"
        >
          {loading ? '⏳' : '🔄'} รีเฟรช
        </button>
      </div>

      {/* Stats */}
      <div className="admin-stats">
        <div className="admin-stat-card">
          <span className="admin-stat-number">{users.length}</span>
          <span className="admin-stat-label">ผู้ใช้ทั้งหมด</span>
        </div>
        <div className="admin-stat-card admin-stat-card-admin">
          <span className="admin-stat-number">{adminCount}</span>
          <span className="admin-stat-label">🛡️ แอดมิน</span>
        </div>
        <div className="admin-stat-card admin-stat-card-user">
          <span className="admin-stat-number">{userCount}</span>
          <span className="admin-stat-label">👤 ผู้ใช้ทั่วไป</span>
        </div>
      </div>

      {/* Filters */}
      <div className="admin-filters">
        <input
          id="admin-search-input"
          className="admin-search-input"
          type="text"
          placeholder="🔍 ค้นหาชื่อ, username, อีเมล..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="admin-filter-tabs">
          {[
            { key: 'all', label: `ทั้งหมด (${users.length})` },
            { key: 'admin', label: `🛡️ แอดมิน (${adminCount})` },
            { key: 'user', label: `👤 ผู้ใช้ (${userCount})` },
          ].map((tab) => (
            <button
              key={tab.key}
              id={`admin-filter-${tab.key}`}
              className={`admin-filter-tab ${filterRole === tab.key ? 'active' : ''}`}
              onClick={() => setFilterRole(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="alert alert-error">
          <span>{error}</span>
          <button className="alert-close" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="admin-loading">
          <div className="admin-spinner" />
          <p>กำลังโหลดข้อมูลผู้ใช้...</p>
        </div>
      ) : filtered.length === 0 ? (
        <p className="empty">ไม่พบผู้ใช้ที่ตรงกับเงื่อนไข</p>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>#</th>
                <th>ชื่อ / Username</th>
                <th>อีเมล</th>
                <th>สถานะ</th>
                <th>บทบาท</th>
                <th>เปลี่ยน Role</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((u) => (
                <tr key={u.id} className={u.status !== 'active' ? 'admin-row-inactive' : ''}>
                  <td className="admin-td-id">{u.id}</td>
                  <td className="admin-td-name">
                    <div className="admin-user-name">{u.full_name || u.username}</div>
                    <div className="admin-user-username">@{u.username}</div>
                  </td>
                  <td className="admin-td-email">{u.email}</td>
                  <td>
                    <span className={`status-pill ${u.status === 'active' ? 'free' : 'busy'}`}>
                      {u.status === 'active' ? 'ใช้งาน' : 'ปิดใช้'}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${u.role === 'admin' ? 'badge-admin' : 'badge-user'}`}>
                      {u.role === 'admin' ? '🛡️ แอดมิน' : '👤 ผู้ใช้ทั่วไป'}
                    </span>
                  </td>
                  <td>
                    {u.id === currentUser?.id ? (
                      <span className="admin-self-label">— ตัวเอง</span>
                    ) : (
                      <button
                        id={`admin-toggle-role-${u.id}`}
                        className={`btn btn-sm ${u.role === 'admin' ? 'btn-danger-sm' : 'btn-primary'}`}
                        onClick={() => handleToggleRole(u)}
                        disabled={updating === u.id}
                      >
                        {updating === u.id
                          ? '⏳...'
                          : u.role === 'admin'
                          ? '⬇️ ลด เป็น User'
                          : '⬆️ เลื่อน เป็น Admin'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="admin-table-foot">แสดง {filtered.length} จาก {users.length} คน</p>
        </div>
      )}
    </div>
  )
}
