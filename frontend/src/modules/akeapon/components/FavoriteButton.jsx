import '../akeapon.css'

// mock: ปุ่มรายการโปรด (localStorage) — ยังไม่เชื่อม backend
export default function FavoriteButton({ active, onToggle }) {
  return (
    <button
      type="button"
      className={`fav-btn ${active ? 'on' : ''}`}
      onClick={onToggle}
      title="รายการโปรด (ต้นแบบ)"
      aria-label="รายการโปรด"
      aria-pressed={active}
    >
      {active ? '♥' : '♡'}
    </button>
  )
}