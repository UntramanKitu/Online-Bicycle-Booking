import { createContext, useContext } from 'react'

export const CurrentUserContext = createContext(null)
export const STORAGE_KEY = 'bikea_current_user_id'

// hook อยู่ไฟล์ .js แยกจาก component เพื่อให้ผ่านกฎ react-refresh/only-export-components
export function useCurrentUser() {
  const ctx = useContext(CurrentUserContext)
  if (!ctx) throw new Error('useCurrentUser must be used inside CurrentUserProvider')
  return ctx
}
