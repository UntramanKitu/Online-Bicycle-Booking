// mock localStorage helpers — ยังไม่เชื่อม backend
export const readStore = (key) => {
  try { return JSON.parse(window.localStorage.getItem(key) || '[]') } catch { return [] }
}
export const writeStore = (key, value) => {
  try { window.localStorage.setItem(key, JSON.stringify(value)) } catch { /* เต็ม/ปิดโหมดส่วนตัว — ข้าม */ }
}