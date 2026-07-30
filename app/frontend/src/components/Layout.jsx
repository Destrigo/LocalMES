import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Factory,
  LayoutDashboard,
  ClipboardList,
  Users,
  Settings,
  LogOut,
  Boxes,
  GitBranch,
  Wrench,
  Monitor,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const linkClass = ({ isActive }) =>
  `flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
    isActive ? 'bg-slate-800 text-white' : 'text-slate-300 hover:bg-slate-800/60'
  }`

export default function Layout({ children }) {
  const { t, i18n } = useTranslation()
  const { user, logout } = useAuth()
  const isBackoffice = user?.role === 'superadmin' || user?.role === 'backoffice'
  const isAdmin = user?.role === 'superadmin'

  return (
    <div className="min-h-screen flex bg-slate-100">
      <aside className="w-60 bg-slate-900 text-white flex flex-col p-4 gap-1">
        <div className="flex items-center gap-2 px-2 py-3 mb-2">
          <Factory size={20} />
          <span className="font-semibold tracking-wide">{t('appName')}</span>
        </div>
        <NavLink to="/dashboard" className={linkClass}>
          <LayoutDashboard size={16} /> {t('nav.dashboard')}
        </NavLink>
        <NavLink to="/shop-floor" className={linkClass}>
          <Wrench size={16} /> {t('nav.shopFloor')}
        </NavLink>
        {isBackoffice && (
          <>
            <NavLink to="/customers" className={linkClass}>
              <Users size={16} /> {t('nav.customers')}
            </NavLink>
            <NavLink to="/work-orders" className={linkClass}>
              <ClipboardList size={16} /> {t('nav.workOrders')}
            </NavLink>
            <NavLink to="/production-orders" className={linkClass}>
              <ClipboardList size={16} /> {t('nav.productionOrders')}
            </NavLink>
            <NavLink to="/products" className={linkClass}>
              <Boxes size={16} /> {t('nav.products')}
            </NavLink>
            <NavLink to="/cycles" className={linkClass}>
              <GitBranch size={16} /> {t('nav.cycles')}
            </NavLink>
            <NavLink to="/lines" className={linkClass}>
              <Factory size={16} /> {t('nav.lines')}
            </NavLink>
          </>
        )}
        {isAdmin && (
          <NavLink to="/settings" className={linkClass}>
            <Settings size={16} /> {t('nav.settings')}
          </NavLink>
        )}
        <a href="/signage" target="_blank" rel="noreferrer" className={linkClass({ isActive: false })}>
          <Monitor size={16} /> {t('nav.signage')}
        </a>
        <div className="mt-auto pt-4 border-t border-slate-700 space-y-2">
          <div className="flex gap-2 px-2">
            <button
              type="button"
              className={`text-xs px-2 py-1 rounded ${i18n.language === 'en' ? 'bg-slate-700' : ''}`}
              onClick={() => { i18n.changeLanguage('en'); localStorage.setItem('localmes_lang', 'en') }}
            >
              EN
            </button>
            <button
              type="button"
              className={`text-xs px-2 py-1 rounded ${i18n.language === 'it' ? 'bg-slate-700' : ''}`}
              onClick={() => { i18n.changeLanguage('it'); localStorage.setItem('localmes_lang', 'it') }}
            >
              IT
            </button>
          </div>
          <div className="px-2 text-xs text-slate-400">{user?.username} · {user?.role}</div>
          <button
            type="button"
            onClick={logout}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-800/60 w-full"
          >
            <LogOut size={16} /> {t('nav.logout')}
          </button>
        </div>
      </aside>
      <main className="flex-1 p-6 overflow-auto">{children}</main>
    </div>
  )
}
