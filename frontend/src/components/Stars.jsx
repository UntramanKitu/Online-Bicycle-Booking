// ดาวให้คะแนนแบบ float (กดครึ่งซ้าย = x.5 ครึ่งขวา = เต็ม เมื่อ allowHalf)
export default function Stars({ value, onPick, allowHalf = false }) {
  const pick = (star, e) => {
    if (!onPick) return
    if (!allowHalf) {
      onPick(star)
      return
    }
    const rect = e.currentTarget.getBoundingClientRect()
    const isLeftHalf = e.clientX - rect.left < rect.width / 2
    onPick(isLeftHalf ? star - 0.5 : star)
  }
  return (
    <div className="stars" role="radiogroup" aria-label="คะแนน">
      {[1, 2, 3, 4, 5].map((s) => (
        <button
          key={s}
          type="button"
          role="radio"
          aria-checked={value === s}
          aria-label={`${s} ดาว`}
          className={`star ${s <= Math.ceil(value) ? 'on' : ''} ${allowHalf && value === s - 0.5 ? 'half' : ''}`}
          onClick={(e) => pick(s, e)}
          disabled={!onPick}
          title={allowHalf ? 'กดครึ่งซ้าย = ครึ่งดาว ครึ่งขวา = เต็มดาว' : `${s} ดาว`}
        >
          ★
        </button>
      ))}
    </div>
  )
}
