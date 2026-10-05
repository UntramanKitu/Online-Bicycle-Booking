import '../akeapon.css'

// mock: กรองเฉพาะรายการโปรด (localStorage) — ยังไม่เชื่อม backend
export default function FavoritesFilter({ count, checked, onChange }) {
  return (
    <label className="fav-filter" title="ต้นแบบ — ยังไม่เชื่อมเซิร์ฟเวอร์">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      ★ เฉพาะรายการโปรด ({count})
    </label>
  )
}