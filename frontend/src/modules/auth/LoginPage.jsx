import { useSearchParams } from 'react-router-dom'
import { authLoginUrl } from '../../api'

export default function LoginPage() {
  const [searchParams] = useSearchParams()
  const error = searchParams.get('error')
  const oauthFailed = error === 'oauth_failed'
  const notRegistered = error === 'user_not_registered'

  return (
    <main className="login-page">
      {/* Background decoration */}
      <div className="login-bg-orb login-bg-orb-1" aria-hidden="true" />
      <div className="login-bg-orb login-bg-orb-2" aria-hidden="true" />

      <div className="login-container">
        {/* Left panel — branding */}
        <section className="login-brand-panel" aria-hidden="true">
          <div className="login-brand-content">
            <div className="login-brand-icon">⌁</div>
            <h2 className="login-brand-title">BikeShare</h2>
            <p className="login-brand-tagline">ระบบจองและยืมจักรยานอัจฉริยะ</p>
            <ul className="login-feature-list">
              <li>🚲 จองจักรยานออนไลน์ได้ทันที</li>
              <li>👥 เข้าร่วมกลุ่มปั่นจักรยาน</li>
              <li>🔔 แจ้งเตือนและติดตามสถานะ</li>
              <li>🛠️ แจ้งปัญหาและการซ่อมบำรุง</li>
            </ul>
          </div>
        </section>

        {/* Right panel — login form */}
        <section className="login-panel">
          <div className="login-mark" aria-hidden="true">⌁</div>
          <p className="login-eyebrow">BIKESHARE MEMBER</p>
          <h1>เข้าสู่ระบบ</h1>
          <p className="login-copy">เข้าสู่ระบบด้วยบัญชี Google เพื่อใช้งานระบบ</p>

          {oauthFailed && (
            <p className="login-error" role="alert">
              ⚠️ เข้าสู่ระบบไม่สำเร็จ หมดเวลาหรือถูกยกเลิก กรุณาลองอีกครั้ง
            </p>
          )}
          {notRegistered && (
            <p className="login-error" role="alert">
              ⛔ บัญชี Google นี้ยังไม่ได้ลงทะเบียนในระบบ กรุณาติดต่อผู้ดูแลเพื่อเปิดใช้งาน
            </p>
          )}

          <a
            id="google-login-btn"
            className="google-login-button"
            href={authLoginUrl}
          >
            <svg className="google-logo-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            เข้าสู่ระบบด้วย Google
          </a>

          <p className="login-note">ระบบจะใช้บัญชี Google เพื่อยืนยันตัวตนเท่านั้น</p>

          {/* Role info cards */}
          <div className="login-roles-section">
            <p className="login-roles-label">บทบาทในระบบ</p>
            <div className="login-role-cards">
              <div className="login-role-card login-role-card-user">
                <div className="login-role-card-icon">👤</div>
                <div className="login-role-card-body">
                  <span className="badge badge-user">ผู้ใช้ทั่วไป</span>
                  <p>จองจักรยาน เข้าร่วมกลุ่มปั่น แจ้งปัญหา ดูข้อมูลของตัวเอง</p>
                </div>
              </div>
              <div className="login-role-card login-role-card-admin">
                <div className="login-role-card-icon">🛡️</div>
                <div className="login-role-card-body">
                  <span className="badge badge-admin">แอดมิน</span>
                  <p>เห็นข้อมูลทุกอย่าง จัดการผู้ใช้ อัพเดทสถานะได้ทั้งระบบ</p>
                </div>
              </div>
            </div>
            <p className="login-note" style={{ marginTop: '10px' }}>
              บทบาทถูกกำหนดจากบัญชีของคุณโดยผู้ดูแลระบบ
            </p>
          </div>
        </section>
      </div>
    </main>
  )
}