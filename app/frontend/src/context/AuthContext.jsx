import { createContext, useContext, useEffect, useState } from 'react'
import api from '../utils/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/auth/me')
      .then((r) => setUser(r.data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const login = async (username, password) => {
    const { data } = await api.post('/auth/login', { username, password })
    setUser(data)
    return data
  }

  const logout = async () => {
    await api.post('/auth/logout')
    setUser(null)
  }

  const changePassword = async (current_password, new_password) => {
    await api.post('/auth/change-password', { current_password, new_password })
    const { data } = await api.get('/auth/me')
    setUser(data)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, changePassword }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
