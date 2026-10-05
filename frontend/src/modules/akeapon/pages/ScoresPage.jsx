import { formatDateTime } from '../../../utils'
import { useCurrentUser } from '../../../context/currentUser'
import '../akeapon.css'

// ข้อมูลจำลอง (mock) — ระบบคะแนนและบทลงโทษจะเชื่อม backend จริงในเฟสถัดไป
const MOCK_SCORE = 85
const MOCK_EVENTS = [
  { id: 1, delta: +10, category: 'reward', reason: 'คืนรถตรงเวลา', created_at: '2026-09-28T10:00:00+07:00' },
  { id: 2, delta: -15, category: 'penalty', reason: 'คืนรถสาย 30 นาที', created_at: '2026-10-01T18:30:00+07:00' },
  { id: 3, delta: +5, category: 'reward', reason: 'รีวิวหลังใช้งานครบถ้วน', created_at: '2026-10-03T09:15:00+07:00' },
  { id: 4, delta: +15, category: 'reward', reason: 'ใช้งานครบ 10 ครั้ง', created_at: '2026-10-05T14:45:00+07:00' },
]
const MOCK_RULES = [
  { type: 'reward', text: 'คืนรถตรงเวลา / ก่อนเวลา', points: '+10 คะแนน' },
  { type: 'reward', text: 'รีวิวหลังคืนรถทุกครั้ง', points: '+5 คะแนน' },
  { type: 'reward', text: 'ใช้งานครบ 10 ครั้ง', points: '+15 คะแนน' },
  { type: 'penalty', text: 'คืนรถสาย (ทุกๆ 15 นาที)', points: '-5 คะแนน' },
  { type: 'penalty', text: 'ไม่มารับรถตามเวลาจอง (no-show)', points: '-20 คะแนน' },
  { type: 'penalty', text: 'ทำรถเสียหาย/สูญหาย', points: '-50 คะแนน' },
]

function levelOf(score) {
  if (score >= 80) return { label: 'ดีเยี่ยม', className: 'free' }
  if (score >= 50) return { label: 'พอใช้', className: 'warn' }
  return { label: 'มีความเสี่ยง', className: 'busy' }
}

export default function ScoresPage() {
  const { currentUser, usersLoading } = useCurrentUser()

  if (!usersLoading && !currentUser) {
    return <p className="empty">กรุณาเข้าสู่ระบบด้วย Google ก่อนใช้งาน</p>
  }

  const level = levelOf(MOCK_SCORE)

  return (
    <div className="page-section">
      <div className="section-head">
        <div>
          <h1 className="section-title">ระบบคะแนนและบทลงโทษ</h1>
          <p className="section-subtitle">พฤติกรรมการใช้งานจักรยานสะสมเป็นคะแนน</p>
        </div>
      </div>

      <div className="alert alert-warn">
        ข้อมูลจำลอง (mock) — หน้านี้ยังไม่เชื่อมเซิร์ฟเวอร์ คะแนนและประวัติเป็นตัวอย่างเพื่อดูดีไซน์ก่อนเท่านั้น
      </div>

      <div className="score-hero">
        <div className="score-main">
          <span className="score-number">{MOCK_SCORE}</span>
          <span className="score-unit">คะแนนสะสม</span>
          <span className={`status-pill ${level.className}`}>ระดับ: {level.label}</span>
        </div>
        <div className="score-side">
          <p>ผู้ใช้: <strong>{currentUser?.full_name || currentUser?.username || '-'}</strong></p>
          <p className="muted small">คะแนน &lt; 50 = ระบบจะจำกัดสิทธิ์การจองชั่วคราว (แผนเฟสถัดไป)</p>
        </div>
      </div>

      <div className="score-grid">
        <section className="ticket-card">
          <header>ประวัติคะแนน</header>
          <ul className="score-events">
            {MOCK_EVENTS.map((e) => (
              <li key={e.id}>
                <span className={`score-delta ${e.delta >= 0 ? 'plus' : 'minus'}`}>{e.delta >= 0 ? `+${e.delta}` : e.delta}</span>
                <span className="score-reason">
                  <strong>{e.reason}</strong>
                  <span className="muted small">{formatDateTime(e.created_at)}</span>
                </span>
                <span className={`status-pill ${e.category === 'reward' ? 'free' : 'busy'}`}>
                  {e.category === 'reward' ? 'รางวัล' : 'บทลงโทษ'}
                </span>
              </li>
            ))}
          </ul>
        </section>

        <section className="ticket-card">
          <header>กติกาคะแนน (ร่าง)</header>
          <ul className="score-events">
            {MOCK_RULES.map((r, i) => (
              <li key={i}>
                <span className={`score-delta ${r.type === 'reward' ? 'plus' : 'minus'}`}>{r.points.split(' ')[0]}</span>
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