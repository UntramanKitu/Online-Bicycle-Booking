import '../akeapon.css'

// กรองเฉพาะรายการโปรด (นับจาก backend)
export default function FavoritesFilter({ count, checked, onChange }) {
  return (
    <label className="fav-filter" title="แสดงเฉพาะจักรยานในรายการโปรด">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      ★ เฉพาะรายการโปรด ({count})
    </label>
  )
}