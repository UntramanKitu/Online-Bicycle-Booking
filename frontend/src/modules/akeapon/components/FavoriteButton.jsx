import '../akeapon.css'

// ปุ่มรายการโปรด (เชื่อม backend) — กดแล้วบันทึกทันที ไม่ต้องไปหน้าอื่น
export default function FavoriteButton({ active, onToggle, busy }) {
  return (
    <button
      type="button"
      className={`fav-btn ${active ? 'on' : ''}`}
      onClick={onToggle}
      disabled={busy}
      title={active ? 'เอาออกจากรายการโปรด' : 'เพิ่มในรายการโปรด'}
      aria-label={active ? 'เอาออกจากรายการโปรด' : 'เพิ่มในรายการโปรด'}
      aria-pressed={active}
    >
      {busy ? '…' : active ? '♥' : '♡'}
    </button>
  )
}