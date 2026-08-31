import MyManager from './components/MyManager'
import './App.css'

export default function App() {
  return (
    <div className="app">
      <header>
        <h1>ระบบจัดการจักรยาน</h1>
      </header>
      <main>
        <MyManager />
      </main>
    </div>
  )
}
