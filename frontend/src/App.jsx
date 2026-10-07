import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { CurrentUserProvider } from './context/CurrentUserContext'
import { useCurrentUser } from './context/currentUser'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import BookingsPage from './modules/chaianan/pages/BookingsPage'
import GroupRidesPage from './modules/chaianan/pages/GroupRidesPage'
import TicketsPage from './modules/chaianan/pages/TicketsPage'
import NotificationsPage from './modules/nathida/pages/NotificationsPage'
import MaintenancePage from './modules/nathida/pages/MaintenancePage'
import ReviewsPage from './modules/nathida/pages/ReviewsPage'
import LoginPage from './modules/auth/LoginPage'
import ScoresPage from './modules/akeapon/pages/ScoresPage'
import FavoritesPage from './modules/akeapon/pages/FavoritesPage'
import LostItemsPage from './modules/akeapon/pages/LostItemsPage'
import AdminDashboard from './modules/auth/AdminDashboard'
import BikesAdminPage from './modules/auth/BikesAdminPage'

function RequireAuth({ children }) {
  const { currentUser, usersLoading } = useCurrentUser()
  const location = useLocation()
  if (usersLoading) return <p className="empty">กำลังตรวจสอบการเข้าสู่ระบบ...</p>
  if (!currentUser) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return children
}

/** Guard สำหรับหน้าที่เฉพาะแอดมินเท่านั้น */
function RequireAdmin({ children }) {
  const { currentUser, isAdmin, usersLoading } = useCurrentUser()
  const location = useLocation()
  if (usersLoading) return <p className="empty">กำลังตรวจสอบสิทธิ์...</p>
  if (!currentUser) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (!isAdmin) return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <CurrentUserProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<RequireAuth><Layout /></RequireAuth>}>
            <Route index element={<HomePage />} />
            <Route path="home" element={<HomePage />} />
            <Route path="bookings" element={<BookingsPage />} />
            <Route path="group-rides" element={<GroupRidesPage />} />
            <Route path="support" element={<TicketsPage />} />
            <Route path="notifications" element={<NotificationsPage />} />
            <Route path="maintenance" element={<MaintenancePage />} />
            <Route path="reviews" element={<ReviewsPage />} />
            <Route path="scores" element={<ScoresPage />} />
            <Route path="favorites" element={<FavoritesPage />} />
            <Route path="lost-items" element={<LostItemsPage />} />
            {/* Admin-only routes */}
            <Route
              path="admin"
              element={
                <RequireAdmin>
                  <AdminDashboard />
                </RequireAdmin>
              }
            />
            <Route
              path="admin/bikes"
              element={
                <RequireAdmin>
                  <BikesAdminPage />
                </RequireAdmin>
              }
            />
            <Route path="*" element={<BookingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </CurrentUserProvider>
  )
}
