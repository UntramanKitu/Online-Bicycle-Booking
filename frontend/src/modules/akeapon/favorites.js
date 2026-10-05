import { useState } from 'react'
import { readStore, writeStore } from './storage'

const FAV_KEY = 'bikea_favorites'

// mock: รายการโปรดเก็บลง localStorage — ยังไม่เชื่อม backend
export function useFavorites() {
  const [favorites, setFavorites] = useState(() => readStore(FAV_KEY))
  const [favOnly, setFavOnly] = useState(false)

  function toggleFavorite(bikeId) {
    setFavorites((prev) => {
      const next = prev.includes(bikeId) ? prev.filter((x) => x !== bikeId) : [...prev, bikeId]
      writeStore(FAV_KEY, next)
      return next
    })
  }

  return { favorites, favOnly, setFavOnly, toggleFavorite }
}