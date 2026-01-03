import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { initCsrf } from '../api'

const initialForm = {
  fullName: '',
  email: '',
  phone: '',
  organization: '',
  password: '',
  passwordConfirm: ''
}

const buildPasswordMessage = (issues) => {
  if (!issues.length) {
    return ''
  }
  return `Пароль должен содержать ${issues.join(', ')}.`
}

export default function Register({ auth }) {
  const [form, setForm] = useState(initialForm)
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    initCsrf()
  }, [])

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
    setErrors((prev) => {
      if (!prev[name]) {
        return prev
      }
      const next = { ...prev }
      delete next[name]
      return next
    })
    if (formError) {
      setFormError('')
    }
  }

  const validateForm = (values) => {
    const nextErrors = {}
    const fullName = values.fullName.trim()
    const email = values.email.trim().toLowerCase()
    const phone = values.phone.trim()
    const organization = values.organization.trim()
    const password = values.password
    const passwordConfirm = values.passwordConfirm

    if (!fullName) {
      nextErrors.fullName = 'Укажите ФИО.'
    } else {
      const parts = fullName.split(/\s+/).filter(Boolean)
      if (parts.length < 2) {
        nextErrors.fullName = 'Укажите фамилию и имя.'
      } else if (parts.some((part) => part.length < 2)) {
        nextErrors.fullName = 'Каждая часть ФИО должна быть минимум из 2 букв.'
      } else if (/[^\p{L}\s'-]/u.test(fullName)) {
        nextErrors.fullName = 'ФИО может содержать только буквы, пробелы и дефисы.'
      }
    }

    if (!email) {
      nextErrors.email = 'Укажите email.'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      nextErrors.email = 'Укажите корректный email.'
    }

    if (!phone) {
      nextErrors.phone = 'Укажите номер телефона.'
    } else {
      const digits = phone.replace(/\D/g, '')
      if (!/^[0-9+()\s.-]+$/.test(phone)) {
        nextErrors.phone = 'Укажите номер телефона в допустимом формате.'
      } else if (digits.length < 10 || digits.length > 15) {
        nextErrors.phone = 'Номер телефона должен содержать от 10 до 15 цифр.'
      }
    }

    if (!organization) {
      nextErrors.organization = 'Укажите организацию.'
    } else if (organization.length < 2) {
      nextErrors.organization = 'Название организации слишком короткое.'
    }

    const passwordIssues = []
    if (password.length < 8) {
      passwordIssues.push('минимум 8 символов')
    }
    if (!/[a-z]/.test(password)) {
      passwordIssues.push('строчную букву')
    }
    if (!/[A-Z]/.test(password)) {
      passwordIssues.push('заглавную букву')
    }
    if (!/\d/.test(password)) {
      passwordIssues.push('цифру')
    }
    if (!/[^A-Za-z0-9]/.test(password)) {
      passwordIssues.push('спецсимвол')
    }
    if (passwordIssues.length) {
      nextErrors.password = buildPasswordMessage(passwordIssues)
    }

    if (!passwordConfirm) {
      nextErrors.passwordConfirm = 'Подтвердите пароль.'
    } else if (passwordConfirm !== password) {
      nextErrors.passwordConfirm = 'Пароли не совпадают.'
    }

    return { nextErrors, email }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSuccess('')
    const { nextErrors, email } = validateForm(form)
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors)
      setFormError('')
      return
    }
    setErrors({})
    setFormError('')
    try {
      await api.post('/auth/register/', {
        full_name: form.fullName.trim(),
        email,
        phone: form.phone.trim(),
        clinic_name: form.organization.trim(),
        password: form.password,
        password_confirm: form.passwordConfirm
      })
      await api.post('/auth/token/', {
        username: email,
        password: form.password
      })
      await auth.onLogin()
      setSuccess('Аккаунт создан!')
      setForm(initialForm)
    } catch (err) {
      const data = err.response?.data
      if (data && typeof data === 'object') {
        const fieldMap = {
          full_name: 'fullName',
          email: 'email',
          phone: 'phone',
          clinic_name: 'organization',
          password: 'password',
          password_confirm: 'passwordConfirm'
        }
        const nextErrors = {}
        Object.entries(data).forEach(([key, value]) => {
          if (key === 'non_field_errors' || key === 'detail') {
            return
          }
          const target = fieldMap[key] || key
          nextErrors[target] = Array.isArray(value) ? value.join(' ') : value
        })
        if (data.non_field_errors) {
          setFormError(Array.isArray(data.non_field_errors) ? data.non_field_errors.join(' ') : data.non_field_errors)
        } else if (data.detail) {
          setFormError(data.detail)
        }
        setErrors(nextErrors)
      } else {
        setFormError('Не удалось зарегистрироваться. Проверьте данные.')
      }
    }
  }

  return (
    <section className="auth">
      <div className="auth-card">
        <h2>Создайте аккаунт</h2>
        <p>Получите доступ к новинкам и наборам для клиники.</p>
        <form onSubmit={handleSubmit}>
          <label>
            ФИО
            <input
              name="fullName"
              value={form.fullName}
              onChange={handleChange}
              autoComplete="name"
              aria-invalid={Boolean(errors.fullName)}
              required
            />
            {errors.fullName && <span className="field-error">{errors.fullName}</span>}
          </label>
          <label>
            Email
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              autoComplete="email"
              aria-invalid={Boolean(errors.email)}
              required
            />
            {errors.email && <span className="field-error">{errors.email}</span>}
          </label>
          <label>
            Телефон
            <input
              type="tel"
              name="phone"
              value={form.phone}
              onChange={handleChange}
              autoComplete="tel"
              aria-invalid={Boolean(errors.phone)}
              required
            />
            {errors.phone && <span className="field-error">{errors.phone}</span>}
          </label>
          <label>
            Организация
            <input
              name="organization"
              value={form.organization}
              onChange={handleChange}
              autoComplete="organization"
              aria-invalid={Boolean(errors.organization)}
              required
            />
            {errors.organization && <span className="field-error">{errors.organization}</span>}
          </label>
          <label>
            Пароль
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              autoComplete="new-password"
              aria-invalid={Boolean(errors.password)}
              required
            />
            <span className="field-hint">
              Минимум 8 символов, заглавная и строчная буквы, цифра и спецсимвол.
            </span>
            {errors.password && <span className="field-error">{errors.password}</span>}
          </label>
          <label>
            Подтверждение пароля
            <input
              type="password"
              name="passwordConfirm"
              value={form.passwordConfirm}
              onChange={handleChange}
              autoComplete="new-password"
              aria-invalid={Boolean(errors.passwordConfirm)}
              required
            />
            {errors.passwordConfirm && <span className="field-error">{errors.passwordConfirm}</span>}
          </label>
          {formError && <div className="error">{formError}</div>}
          {success && <div className="success">{success}</div>}
          <button type="submit">Создать аккаунт</button>
        </form>
        <p className="helper">
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </p>
      </div>
    </section>
  )
}
