import { useEffect, useState } from 'react'
import { api, getApiError } from '../../../api'
import { formatDateTime } from '../../../utils'
import { useCurrentUser } from '../../../context/currentUser'

export default function NotificationsPage() {
  const { userId, currentUser, usersLoading, isAdmin, getUserName } = useCurrentUser()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState(null)
  // มุมมองของแอดมิน: mine = ของตัวเอง (default), all = แจ้งเตือนทุกคนในระบบ
  const [scope, setScope] = useState('mine')

  async function load(nextScope = scope) {
    setLoading(true)
    try {
      const res = nextScope === 'all' && isAdmin
        ? await api.get('/notifications')
        : await api.get(`/notifications/user/${userId}`)
      setItems(res.data)
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (usersLoading || !userId) return
    const timer = window.setTimeout(() => load(scope), 0)
    return () => window.clearTimeout(timer)
  }, [userId, usersLoading, scope]) // eslint-disable-line react-hooks/exhaustive-deps

  function switchScope(next) {
    if (next === scope) return
    setMessage(null)
    setScope(next)
  }

  async function markRead(id) {
    try {
      await api.patch(`/notifications/${id}/read`)
      setItems((list) => list.map((n) => (n.id === id ? { ...n, is_read: true } : n)))
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    }
  }

  const unread = items.filter((n) => !n.is_read).length
  const readCount = items.length - unread

  async function clearRead() {
    try {
      const res = await api.delete(`/notifications/user/${userId}/read`)
      setItems((list) => list.filter((n) => !n.is_read))
      setMessage({ type: 'success', text: `ล้างข้อความที่อ่านแล้ว ${res.data?.deleted ?? 0} รายการ` })
    } catch (err) {
      setMessage({ type: 'error', text: getApiError(err) })
    }
  }

  if (!usersLoading && !currentUser) {
    return <p className="empty">กรุณาเข้าสู่ระบบด้วย Google ก่อนใช้งาน</p>
  }

  return (
    <div className="page-section">
      <div className="section-head">
        <div>
          <h1 className="section-title">การแจ้งเตือน</h1>
          <p className="section-subtitle">
            {scope === 'all'
              ? `มุมมองแอดมิน — แจ้งเตือนของผู้ใช้ทุกคน ${items.length} รายการ (ยังไม่ได้อ่าน ${unread} รายการ)`
              : `ทั้งหมด ${items.length} รายการ — ยังไม่ได้อ่าน ${unread} รายการ`}
          </p>
        </div>
        <div className="section-head-actions">
          {isAdmin && (
            <div className="tabs">
              <button className={`tab ${scope === 'mine' ? 'active' : ''}`} onClick={() => switchScope('mine')}>
                ของฉัน
              </button>
              <button className={`tab ${scope === 'all' ? 'active' : ''}`} onClick={() => switchScope('all')}>
                ทั้งระบบ
              </button>
            </div>
          )}
          {scope === 'mine' && readCount > 0 && <button className="btn btn-ghost" onClick={clearRead}>ล้างที่อ่านแล้ว ({readCount})</button>}
          <button className="btn btn-ghost" onClick={() => load()}>รีเฟรช</button>
        </div>
      </div>

      {message && (
        <div className={`alert ${message.type === 'error' ? 'alert-error' : 'alert-success'}`}>
          {message.text}
          <button className="alert-close" onClick={() => setMessage(null)}>×</button>
        </div>
      )}

      {loading ? (
        <p className="empty">กำลังโหลดข้อมูล...</p>
      ) : items.length === 0 ? (
        <p className="empty">ยังไม่มีการแจ้งเตือน</p>
      ) : (
        <div className="ticket-cards">
          {items.map((n) => (
            <article className={`ticket-card ${n.is_read ? '' : 'status-open'}`} key={n.id}>
              <div className="ticket-card-head">
                <h3>{n.title}</h3>
                {!n.is_read && <span className="badge badge-danger">ใหม่</span>}
              </div>
              <p>{n.message}</p>
              <div className="ticket-card-badges">
                {scope === 'all' && <span className="badge badge-muted">ถึง {getUserName(n.user_id)}</span>}
                <span className="muted small">{formatDateTime(n.created_at)}</span>
              </div>
              {!n.is_read && (
                <div className="ticket-card-actions">
                  <button className="btn btn-sm btn-primary" onClick={() => markRead(n.id)}>
                    ทำเป็นอ่านแล้ว
                  </button>
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
