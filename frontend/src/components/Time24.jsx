// ตัวเลือกเวลาแบบ 24 ชั่วโมง (ไม่ใช้ AM/PM)
// native input type="time"/"datetime-local" จะแสดง AM/PM ตาม locale ของเบราว์เซอร์
// จึงใช้ <select> ชั่วโมง/นาที แทน เพื่อให้แสดงรูปแบบ 24 ชั่วโมงเสมอ
const pad2 = (n) => String(n).padStart(2, '0')
const HOURS = Array.from({ length: 24 }, (_, i) => pad2(i))

// ตัวเลือกนาทีทุก 5 นาที (คงค่าเดิมที่ไม่ลงตัว 5 ไว้ เช่น 18:47)
function minuteList(minute) {
  const opts = []
  for (let m = 0; m < 60; m += 5) opts.push(m)
  if (Number.isInteger(minute) && minute % 5 !== 0) opts.push(minute)
  return opts
}

export function Time24({ value, onChange, required = false }) {
  const [hh = '', mm = ''] = String(value || '').split(':')
  const pickHour = (v) => onChange(`${v}:${mm || '00'}`)
  const pickMinute = (v) => onChange(`${hh || '00'}:${v}`)
  return (
    <div className="time24">
      <select aria-label="ชั่วโมง" value={hh} onChange={(e) => pickHour(e.target.value)} required={required}>
        <option value="" disabled>ชั่วโมง</option>
        {HOURS.map((h) => <option key={h} value={h}>{h}</option>)}
      </select>
      <span className="time24-sep" aria-hidden="true">นาฬิกา</span>
      <select aria-label="นาที" value={mm} onChange={(e) => pickMinute(e.target.value)} required={required}>
        <option value="" disabled>นาที</option>
        {minuteList(Number(mm)).map((m) => <option key={m} value={pad2(m)}>{pad2(m)}</option>)}
      </select>
      <span className="time24-sep" aria-hidden="true">น.</span>
      <span className="time24-suffix">น. (24 ชม.)</span>
    </div>
  )
}

// วัน + เวลา แบบ 24 ชั่วโมง — ค่าที่ส่งออกเป็น "YYYY-MM-DDTHH:MM" เหมือน datetime-local
export function DateTime24({ value, onChange, required = false }) {
  const [datePart = '', timePart = ''] = String(value || '').split('T')
  const today = () => {
    const d = new Date()
    return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`
  }
  return (
    <div className="datetime24">
      <input
        type="date"
        aria-label="วันที่"
        value={datePart}
        onChange={(e) => onChange(`${e.target.value}T${timePart || '00:00'}`)}
        required={required}
      />
      <Time24 value={timePart} onChange={(tp) => onChange(`${datePart || today()}T${tp}`)} required={required} />
    </div>
  )
}