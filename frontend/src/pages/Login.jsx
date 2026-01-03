import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { initCsrf } from '../api'

export default function Login({ auth }) {
  const [form, setForm] = useState({ login: '', password: '' })
  const [error, setError] = useState('')

  useEffect(() => {
    initCsrf()
  }, [])

  const handleChange = (event) => {
    setForm({ ...form, [event.target.name]: event.target.value })
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    try {
      const rawLogin = form.login.trim()
      const loginValue = rawLogin.includes('@') ? rawLogin.toLowerCase() : rawLogin
      await api.post('/auth/token/', {
        username: loginValue,
        password: form.password
      })
      await auth.onLogin()
    } catch (err) {
      setError('Неверные данные. Попробуйте еще раз.')
    }
  }

  return (
    <section className="auth">
      <div className="auth-card">
        <h2>С возвращением</h2>
        <p>Войдите, чтобы управлять заказами и закупками клиники.</p>
        <form onSubmit={handleSubmit}>
          <label>
            Email или логин
            <input
              name="login"
              value={form.login}
              onChange={handleChange}
              autoComplete="username"
              required
            />
          </label>
          <label>
            Пароль
            <input type="password" name="password" value={form.password} onChange={handleChange} required />
          </label>
          {error && <div className="error">{error}</div>}
          <button type="submit">Войти</button>
        </form>
        <p className="helper">
          Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
        </p>
      </div>
    </section>
  )
}
