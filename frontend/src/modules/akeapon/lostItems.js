import { useState } from 'react'
import { readStore, writeStore } from './storage'

const LOST_KEY = 'bikea_lost_items'

// mock: การแจ้งของหายเก็บลง localStorage — ยังไม่เชื่อม backend
export function useLostItems() {
  const [lostItems, setLostItems] = useState(() => readStore(LOST_KEY))
  const [lostFor, setLostFor] = useState(null)

  function openLost(booking) {
    setLostFor(booking)
  }

  function closeLost() {
    setLostFor(null)
  }

  function saveLostItem(entry) {
    const next = [entry, ...lostItems]
    setLostItems(next)
    writeStore(LOST_KEY, next)
    setLostFor(null)
  }

  return { lostItems, lostFor, openLost, closeLost, saveLostItem }
}