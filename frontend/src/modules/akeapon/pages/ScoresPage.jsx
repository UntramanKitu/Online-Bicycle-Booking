import { useEffect, useState } from 'react'
import { api, getApiError } from '../../../api'
import { formatDateTime } from '../../../utils'
import { useCurrentUser } from '../../../context/currentUser'
import '../akeapon.css'

// ระบบคะแนนพฤติกรรม — คอลัมน์ points ในตาราง accounts_unifieduser (เริ่มต้น 12, ต่ำสุด 0)
const MAX_POINTS = 12

const REASON_LABELS = {
  late_return: 'คืนรถสาย',
  damaged: 'ทำรถเสียหาย',
  lost: 'ทำรถสูญหาย',
  other: 'อื่นๆ',
  good_behavior: 'พฤติกรรมดี',
  no_violation_week: 'ไม่ทำผิดตลอดสัปดาห์',
}

const ACTION_LABELS = {
  warning: 'ตักเตือน',
  suspension: 'พักสิทธิ์',
  ban: 'ระงับการใช้งาน',
}

const POSITIVE_REASONS = new Set(['good_behavior', 'no_violation_week'])

const RULES = [
  { type: 'penalty', text: 'คืนรถสาย (ทุกๆ 15 นาที)', points: '-1' },
  { type: 'penalty', text: 'ไม่มารับรถตามเวลาจอง (no-show)', points: '-1' },
  { type: 'penalty', text: 'ทำรถเสียหาย/สูญหาย', points: '-1' },
  { type: 'reward', text: 'พฤติกรรมดี / ไม่ทำผิดตลอดสัปดาห์', points: '+1' },
]

function levelOf(points) {
  if (points >= 10) return { label: 'ดีเยี่ยม', className: 'free' }
  if (points >= 6) return { label: 'พอใช้', className: 'warn' }
  return { label: 'มีความเสี่ยง', className: 'busy' }
}

export default function ScoresPage() {
  const { userId, currentUser, usersLoading } = useCurrentUser()
  const [strikes, setStrikes] = useState([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    if (usersLoading || !userId) return
    // เลื่อนไป task ถัดไป — กันกฎ react-hooks/set-state-in-effect
    const timer = window.setTimeout(async () => {
      try {
        const res = await api.get(`/penalties/user/${userId}`)
        setStrikes(res.data || [])
      } catch (err) {
        setMessage(getApiError(err))
      } finally {
        setLoading(false)
      }
    }, 0)
    return () => window.clearTimeout(timer)
  }, [userId, usersLoading])

  if (!usersLoading && !currentUser) {
    return <p className="empty">กรุณาเข้าสู่ระบบก่อนใช้งาน</p>
  }

  const points = typeof currentUser?.points === 'number' ? currentUser.points : MAX_POINTS
  const level = levelOf(points)

  return (
    <div className="page-section">
      <div className="section-head">
        <div>
          <h1 className="section-title">ระบบคะแนนและบทลงโทษ</h1>
          <p className="section-subtitle">พฤติกรรมการใช้งานจักรยานสะสมเป็นคะแนน (จากเซิร์ฟเวอร์จริง)</p>
        </div>
      </div>

      {message && <div className="alert alert-error">{message}</div>}

      <div className="score-hero">
        <div className="score-main">
          <span className="score-number">{points}</span>
          <span className="score-unit">/ {MAX_POINTS} คะแนน</span>
          <span className={`status-pill ${level.className}`}>ระดับ: {level.label}</span>
        </div>
        <div className="score-side">
          <p>ผู้ใช้: <strong>{currentUser?.full_name || currentUser?.username || '-'}</strong></p>
          <p className="muted small">คะแนน &lt; 6 = ระบบจะจำกัดสิทธิ์การจองชั่คราว (แผนเฟสถัดไป)</p>
        </div>
      </div>

      <div className="score-grid">
        <section className="ticket-card">
          <header>ประวัติคะแนน</header>
          {loading ? (
            <p className="empty small">กำลังโหลด...</p>
          ) : strikes.length === 0 ? (
            <p className="empty small">ยังไม่มีประวัติลงโทษ — ทำได้ดีมาก! 🎉</p>
          ) : (
            <ul className="score-events">
              {strikes.map((s) => {
                const positive = POSITIVE_REASONS.has(s.reason)
                return (
                  <li key={s.id}>
                    <span className={`score-delta ${positive ? 'plus' : 'minus'}`}>
                      {positive ? `+${s.penalty_points}` : `-${s.penalty_points}`}
                    </span>
                    <span className="score-reason">
                      <strong>{REASON_LABELS[s.reason] || s.reason}</strong>
                      <span className="muted small">
                        {ACTION_LABELS[s.action] || s.action}
                        {s.suspension_days ? ` ${s.suspension_days} วัน` : ''} · {formatDateTime(s.created_at)}
                      </span>
                    </span>
                    <span className={`status-pill ${positive ? 'free' : 'busy'}`}>
                      {s.completed ? 'ปิดเคสแล้ว' : positive ? 'รางวัล' : 'บทลงโทษ'}
                    </span>
                  </li>
                )
              })}
            </ul>
          )}
        </section>

        <section className="ticket-card">
          <header>กติกาคะแนน</header>
          <ul className="score-events">
            {RULES.map((r, i) => (
              <li key={i}>
                <span className={`score-delta ${r.type === 'reward' ? 'plus' : 'minus'}`}>{r.points}</span>
                <span className="score-reason">{r.text}</span>
                <span className={`status-pill ${r.type === 'reward' ? 'free' : 'busy'}`}>
                  {r.type === 'reward' ? 'รางวัล' : 'บทลงโทษ'}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}
