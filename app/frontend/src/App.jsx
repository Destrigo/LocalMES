import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import ChangePassword from './pages/ChangePassword'
import {
  Dashboard,
  Customers,
  WorkOrders,
  ProductionOrders,
  Products,
  Cycles,
  Lines,
  ShopFloor,
  SettingsPage,
  Signage,
} from './pages/Resources'

function Protected({ children, backoffice, admin }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <div className="min-h-screen flex items-center justify-center text-slate-400">…</div>
  if (!user) return <Navigate to="/login" state={{ from: location.pathname }} replace />
  if (user.must_change_password && location.pathname !== '/change-password') {
    return <Navigate to="/change-password" replace />
  }
  if (admin && user.role !== 'superadmin') return <Navigate to="/dashboard" replace />
  if (backoffice && user.role === 'operator') return <Navigate to="/dashboard" replace />
  return children
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/signage" element={<Signage />} />
      <Route path="/login" element={<Login />} />
      <Route path="/change-password" element={<ChangePassword />} />
      <Route path="/dashboard" element={<Protected><Layout><Dashboard /></Layout></Protected>} />
      <Route path="/shop-floor" element={<Protected><Layout><ShopFloor /></Layout></Protected>} />
      <Route path="/customers" element={<Protected backoffice><Layout><Customers /></Layout></Protected>} />
      <Route path="/work-orders" element={<Protected backoffice><Layout><WorkOrders /></Layout></Protected>} />
      <Route path="/production-orders" element={<Protected backoffice><Layout><ProductionOrders /></Layout></Protected>} />
      <Route path="/products" element={<Protected backoffice><Layout><Products /></Layout></Protected>} />
      <Route path="/cycles" element={<Protected backoffice><Layout><Cycles /></Layout></Protected>} />
      <Route path="/lines" element={<Protected backoffice><Layout><Lines /></Layout></Protected>} />
      <Route path="/settings" element={<Protected admin><Layout><SettingsPage /></Layout></Protected>} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster position="top-right" />
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
