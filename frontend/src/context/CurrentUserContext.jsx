import { createContext, useContext, useEffect, useState } from 'react'

const CurrentUserContext = createContext(null)
const STORAGE_KEY = 'bikea_current_user_id'

export function CurrentUserProvider({ children }) {
  const [userId, setUserId] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved ? Number(saved) : 1
  })

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, String(userId))
  }, [userId])

  return (
    <CurrentUserContext.Provider value={{ userId, setUserId }}>
      {children}
    </CurrentUserContext.Provider>
  )
}

export function useCurrentUser() {
  const ctx = useContext(CurrentUserContext)
  if (!ctx) throw new Error('useCurrentUser ต้องใช้ภายใน CurrentUserProvider')
  return ctx
}