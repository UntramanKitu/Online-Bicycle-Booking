import { useState } from 'react'
import ReturnsManager from './components/ReturnsManager'
import DamagesManager from './components/DamagesManager'
import FavoritesManager from './components/FavoritesManager'
import './App.css'

const TABS = [
  { key: 'returns', label: 'บันทึกการคืน', icon: '🚲' },
  { key: 'damages', label: 'ความเสียหาย', icon: '🔧' },
  { key: 'favorites', label: 'รายการโปรด', icon: '⭐' },
]

export default function App() {
  const [tab, setTab] = useState('returns')

  return (
    <div className="app">
      <header>
        <h1>ระบบจัดการการคืนจักรยาน</h1>
        <nav>
          {TABS.map(t => (
            <button
              key={t.key}
              className={tab === t.key ? 'active' : ''}
              onClick={() => setTab(t.key)}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </nav>
      </header>
      <main>
        {tab === 'returns' && <ReturnsManager />}
        {tab === 'damages' && <DamagesManager />}
        {tab === 'favorites' && <FavoritesManager />}
      </main>
    </div>
  )
}
