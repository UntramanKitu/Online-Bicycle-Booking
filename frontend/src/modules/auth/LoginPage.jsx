import { authLoginUrl } from '../../api'

export default function LoginPage() {
  return (
    <main className="login-page">
      <section className="login-panel">
        <div className="login-mark" aria-hidden="true">⌁</div>
        <p className="login-eyebrow">BIKESHARE MEMBER</p>
        <h1>เข้าสู่ระบบ</h1>
        <p className="login-copy">เข้าสู่ระบบเพื่อจองจักรยาน เข้าร่วมกลุ่มปั่น และแจ้งปัญหาการใช้งาน</p>
        <a className="google-login-button" href={authLoginUrl}>
          <span className="google-logo" aria-hidden="true">G</span>
          เข้าสู่ระบบด้วย Google
        </a>
        <p className="login-note">ระบบจะใช้บัญชี Google เพื่อยืนยันตัวตนเท่านั้น</p>
      </section>
    </main>
  )
}