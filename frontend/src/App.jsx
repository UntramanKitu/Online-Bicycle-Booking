import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { CurrentUserProvider } from './context/CurrentUserContext'
import Layout from './components/Layout'
import BookingsPage from './modules/chaiyanan/pages/BookingsPage'
import GroupRidesPage from './modules/chaiyanan/pages/GroupRidesPage'
import TicketsPage from './modules/chaiyanan/pages/TicketsPage'
import LoginPage from './modules/auth/LoginPage'

export default function App() {
  return (
    <CurrentUserProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<Layout />}>
            <Route index element={<BookingsPage />} />
            <Route path="bookings" element={<BookingsPage />} />
            <Route path="group-rides" element={<GroupRidesPage />} />
            <Route path="support" element={<TicketsPage />} />
            <Route path="*" element={<BookingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </CurrentUserProvider>
  )
}
