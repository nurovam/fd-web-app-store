import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export default function Cart({ auth }) {
  const navigate = useNavigate()
  const [cart, setCart] = useState(null)
  const [status, setStatus] = useState({ type: '', message: '' })
  const [loading, setLoading] = useState(false)
  const [isCheckoutOpen, setIsCheckoutOpen] = useState(false)
  const [checkoutForm, setCheckoutForm] = useState({
    fullName: '',
    phone: '',
    address: '',
    clinicName: ''
  })
  const [formError, setFormError] = useState('')

  const loadCart = () => {
    setLoading(true)
    api
      .get('/cart/')
      .then((response) => setCart(response.data))
      .catch(() => setStatus({ type: 'error', message: 'Не удалось загрузить корзину.' }))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!auth?.isAuthenticated) {
      navigate('/login')
      return
    }
    loadCart()
  }, [auth, navigate])

  const total = useMemo(() => {
    if (!cart?.items?.length) return 0
    return cart.items.reduce((sum, item) => {
      const price = Number(item.variant?.price ?? item.product?.price ?? 0)
      return sum + price * item.quantity
    }, 0)
  }, [cart])

  const updateQuantity = async (itemId, quantity) => {
    if (quantity < 1) return
    setStatus({ type: '', message: '' })
    try {
      const response = await api.patch(`/cart/items/${itemId}/`, { quantity })
      setCart(response.data)
    } catch (err) {
      setStatus({ type: 'error', message: 'Не удалось обновить количество.' })
    }
  }

  const removeItem = async (itemId) => {
    setStatus({ type: '', message: '' })
    try {
      await api.delete(`/cart/items/${itemId}/`)
      loadCart()
    } catch (err) {
      setStatus({ type: 'error', message: 'Не удалось удалить позицию.' })
    }
  }

  const handleCheckout = async () => {
    if (!cart?.items?.length) return
    setFormError('')
    setStatus({ type: '', message: '' })
    setIsCheckoutOpen(true)
  }

  const handleFormChange = (event) => {
    setCheckoutForm({ ...checkoutForm, [event.target.name]: event.target.value })
  }

  const submitOrder = async (event) => {
    event.preventDefault()
    setFormError('')
    const { fullName, phone, address, clinicName } = checkoutForm
    if (!fullName || !phone || !address || !clinicName) {
      setFormError('Заполните все поля.')
      return
    }
    setLoading(true)
    try {
      await api.patch('/account/profile/', {
        full_name: fullName,
        phone,
        clinic_name: clinicName
      })
      const addressResponse = await api.post('/account/addresses/', {
        label: 'Доставка',
        line1: address,
        line2: '',
        city: 'Душанбе',
        region: '',
        postal_code: '',
        country: 'Tajikistan',
        is_default: true
      })
      await api.post('/orders/', { address_id: addressResponse.data.id })
      setStatus({ type: 'success', message: 'Заказ оформлен! Мы скоро свяжемся.' })
      setIsCheckoutOpen(false)
      setCheckoutForm({ fullName: '', phone: '', address: '', clinicName: '' })
      loadCart()
    } catch (err) {
      const message = err?.response?.data?.detail || 'Не удалось оформить заказ.'
      setStatus({ type: 'error', message })
    } finally {
      setLoading(false)
    }
  }

  if (!auth?.isAuthenticated) {
    return null
  }

  return (
    <section className="cart-page">
      <div className="cart-header">
        <h2>Корзина</h2>
        <p>Проверьте выбранные позиции перед оформлением заказа.</p>
      </div>
      <div className="cart-grid">
        <div className="cart-list">
          {cart?.items?.length ? (
            cart.items.map((item) => (
              <article key={item.id} className="cart-item">
                <div className="cart-item-media">
                  {item.product?.image_url ? (
                    <img src={item.product.image_url} alt={item.product?.name} />
                  ) : (
                    <div className="placeholder">Нет изображения</div>
                  )}
                </div>
                <div className="cart-item-body">
                  <div>
                    <h3>{item.product?.name}</h3>
                    <p className="muted">
                      {item.product?.category?.name}
                      {item.variant?.label ? ` · ${item.variant.label}` : ''}
                    </p>
                  </div>
                  <div className="cart-item-meta">
                    <span className="price">
                      {item.variant?.price ?? item.product?.price} c.
                    </span>
                    <div className="qty-controls">
                      <button type="button" className="ghost" onClick={() => updateQuantity(item.id, item.quantity - 1)}>
                        −
                      </button>
                      <span>{item.quantity}</span>
                      <button type="button" className="ghost" onClick={() => updateQuantity(item.id, item.quantity + 1)}>
                        +
                      </button>
                    </div>
                    <button type="button" className="text-button" onClick={() => removeItem(item.id)}>
                      Удалить
                    </button>
                  </div>
                </div>
              </article>
            ))
          ) : (
            <div className="panel">Корзина пуста.</div>
          )}
        </div>
        <aside className="cart-summary">
          <h3>Итого</h3>
          <div className="cart-total">
            <span>Сумма заказа</span>
            <strong>{total.toFixed(2)} c.</strong>
          </div>
          <button type="button" onClick={handleCheckout} disabled={loading || !cart?.items?.length}>
            Оформить заказ
          </button>
          <p className="muted">Подтверждение и доставка обсуждаются менеджером.</p>
          {status.message && (
            <div className={status.type === 'error' ? 'error' : 'success'}>{status.message}</div>
          )}
        </aside>
      </div>
      {isCheckoutOpen && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal">
            <div className="modal-header">
              <h3>Данные для заказа</h3>
              <button
                type="button"
                className="icon-button"
                aria-label="Закрыть"
                onClick={() => setIsCheckoutOpen(false)}
              >
                ×
              </button>
            </div>
            <form className="modal-body" onSubmit={submitOrder}>
              <label>
                ФИО
                <input name="fullName" value={checkoutForm.fullName} onChange={handleFormChange} required />
              </label>
              <label>
                Телефон
                <input name="phone" value={checkoutForm.phone} onChange={handleFormChange} required />
              </label>
              <label>
                Адрес доставки
                <input name="address" value={checkoutForm.address} onChange={handleFormChange} required />
              </label>
              <label>
                Название клиники
                <input name="clinicName" value={checkoutForm.clinicName} onChange={handleFormChange} required />
              </label>
              {formError && <div className="error">{formError}</div>}
              <div className="modal-actions">
                <button type="button" className="ghost" onClick={() => setIsCheckoutOpen(false)}>
                  Отмена
                </button>
                <button type="submit" disabled={loading}>
                  Подтвердить заказ
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  )
}
