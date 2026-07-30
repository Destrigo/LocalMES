import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext'

export default function ChangePassword() {
  const { t } = useTranslation()
  const { user, changePassword } = useAuth()
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)

  if (!user) return <Navigate to="/login" replace />
  if (done || !user.must_change_password) return <Navigate to="/dashboard" replace />

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await changePassword(current, next)
      setDone(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 px-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm bg-white rounded-xl p-6 shadow space-y-4">
        <h1 className="text-lg font-semibold">{t('changePassword.title')}</h1>
        <input
          type="password"
          placeholder={t('changePassword.current')}
          className="w-full border rounded-lg px-3 py-2"
          value={current}
          onChange={(e) => setCurrent(e.target.value)}
        />
        <input
          type="password"
          placeholder={t('changePassword.next')}
          className="w-full border rounded-lg px-3 py-2"
          value={next}
          onChange={(e) => setNext(e.target.value)}
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" className="w-full bg-slate-900 text-white rounded-lg py-2">
          {t('changePassword.submit')}
        </button>
      </form>
    </div>
  )
}
