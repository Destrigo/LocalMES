import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { t } = useTranslation()
  const { user, login } = useAuth()
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) {
    if (user.must_change_password) return <Navigate to="/change-password" replace />
    return <Navigate to="/dashboard" replace />
  }

  const onSubmit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await login(username, password)
    } catch {
      setError(t('login.error'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm bg-white rounded-xl p-6 shadow-xl space-y-4">
        <h1 className="text-xl font-semibold text-slate-800">{t('appName')}</h1>
        <p className="text-sm text-slate-500">{t('login.title')}</p>
        <label className="block text-sm">
          <span className="text-slate-600">{t('login.username')}</span>
          <input
            className="mt-1 w-full border rounded-lg px-3 py-2"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
          />
        </label>
        <label className="block text-sm">
          <span className="text-slate-600">{t('login.password')}</span>
          <input
            type="password"
            className="mt-1 w-full border rounded-lg px-3 py-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={busy}
          className="w-full bg-slate-900 text-white rounded-lg py-2 font-medium disabled:opacity-60"
        >
          {t('login.submit')}
        </button>
      </form>
    </div>
  )
}
