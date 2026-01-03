import { useEffect, useMemo, useState } from 'react'
import { Link, Route, Routes, useNavigate } from 'react-router-dom'
import api, { initCsrf } from './api'
import Catalog from './pages/Catalog'
import Cart from './pages/Cart'
import Account from './pages/Account'
import Login from './pages/Login'
import Register from './pages/Register'
import ServicePortal from './pages/ServicePortal'

export default function App() {
  const navigate = useNavigate()
  const [user, setUser] = useState(undefined)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  const loadUser = async () => {
    try {
      const response = await api.get('/account/me/')
      setUser(response.data)
      setIsAuthenticated(true)
      return true
    } catch (err) {
      setUser(null)
      setIsAuthenticated(false)
      return false
    }
  }

  useEffect(() => {
    initCsrf()
    loadUser()
  }, [])

  const handleLogin = async () => {
    await loadUser()
    navigate('/catalog')
  }

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout/')
    } catch (err) {}
    setUser(null)
    setIsAuthenticated(false)
    navigate('/login')
  }

  const authContext = useMemo(
    () => ({
      isAuthenticated,
      user,
      onLogin: handleLogin,
      onLogout: handleLogout
    }),
    [isAuthenticated, user]
  )

  return (
    <div className="app">
      <header className="site-header">
        <div className="topbar">
          <div className="topbar-left">
            <span>г. Душанбе · FamilyDent</span>
            <span>Пн-Сб 09:00 — 19:00</span>
          </div>
          <div className="topbar-right">
            <a href="tel:+992900000000">+992 90 000 00 00</a>
            <a href="mailto:info@familydent.tj">info@familydent.tj</a>
          </div>
        </div>
        <div className="header-main">
          <div className="brand">
            <span className="logo">FD</span>
            <div>
              <h1>FamilyDent Маркет</h1>
              <p>Товары, материалы и сервис для клиник</p>
            </div>
          </div>
          <nav>
            <Link to="/catalog">Каталог</Link>
            <Link to="/cart">Корзина</Link>
            {isAuthenticated && <Link to="/account">Личный кабинет</Link>}
            {user?.is_staff && <Link to="/service">Сервисный кабинет</Link>}
            {isAuthenticated ? (
              <button className="ghost" onClick={handleLogout}>Выйти</button>
            ) : (
              <Link to="/login" className="nav-button">Войти</Link>
            )}
          </nav>
        </div>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Catalog auth={authContext} />} />
          <Route path="/catalog" element={<Catalog auth={authContext} />} />
          <Route path="/cart" element={<Cart auth={authContext} />} />
          <Route path="/account" element={<Account auth={authContext} />} />
          <Route path="/login" element={<Login auth={authContext} />} />
          <Route path="/register" element={<Register auth={authContext} />} />
          <Route path="/service" element={<ServicePortal auth={authContext} />} />
        </Routes>
      </main>
      <footer className="site-footer">
        <div>FamilyDent TJ · Интернет‑магазин стоматологии</div>
        <div>Вопросы? info@familydent.tj</div>
      </footer>
    </div>
  )
}
