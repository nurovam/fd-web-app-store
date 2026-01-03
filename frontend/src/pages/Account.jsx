import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

const statusLabels = {
  pending: 'Ожидает',
  paid: 'Оплачен',
  shipped: 'Отправлен',
  received: 'Получен',
  canceled: 'Отменен'
}

const paymentLabels = {
  pending: 'Ожидает',
  paid: 'Оплачен',
  failed: 'Ошибка'
}

const formatDate = (value) => {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('ru-RU')
}

const extractList = (payload) => (Array.isArray(payload) ? payload : payload?.results || [])

export default function Account({ auth }) {
  const navigate = useNavigate()
  const [orders, setOrders] = useState([])
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState({ type: '', message: '' })
  const [documentView, setDocumentView] = useState(null)
  const [pdfLoading, setPdfLoading] = useState(false)
  const [cancelingId, setCancelingId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    if (!auth?.isAuthenticated) {
      navigate('/login')
      return
    }
    loadProfile()
    loadOrders()
  }, [auth, navigate])

  const loadOrders = () => {
    setLoading(true)
    api
      .get('/orders/?page_size=100')
      .then((response) => setOrders(extractList(response.data)))
      .catch(() => setStatus({ type: 'error', message: 'Не удалось загрузить заказы.' }))
      .finally(() => setLoading(false))
  }

  const loadProfile = () => {
    api
      .get('/account/profile/')
      .then((response) => setProfile(response.data))
      .catch(() => setProfile(null))
  }

  const handleReorder = async (order) => {
    if (!order?.items?.length) return
    setStatus({ type: '', message: '' })
    setLoading(true)
    try {
      await Promise.all(
        order.items.map((item) =>
          api.post('/cart/', {
            product_id: item.product?.id,
            variant_id: item.variant?.id || null,
            quantity: item.quantity
          })
        )
      )
      navigate('/cart')
    } catch (err) {
      setStatus({ type: 'error', message: 'Не удалось повторить заказ.' })
    } finally {
      setLoading(false)
    }
  }

  const handleCancelOrder = async (orderId) => {
    setStatus({ type: '', message: '' })
    setCancelingId(orderId)
    try {
      await api.post(`/orders/${orderId}/cancel/`)
      setStatus({ type: 'success', message: 'Заказ отменен.' })
      loadOrders()
    } catch (err) {
      const message = err?.response?.data?.detail || 'Не удалось отменить заказ.'
      setStatus({ type: 'error', message })
    } finally {
      setCancelingId(null)
    }
  }

  const handleDeleteOrder = async (orderId) => {
    setStatus({ type: '', message: '' })
    setDeletingId(orderId)
    try {
      await api.delete(`/orders/${orderId}/`)
      setStatus({ type: 'success', message: 'Заказ удален.' })
      loadOrders()
    } catch (err) {
      const message = err?.response?.data?.detail || 'Не удалось удалить заказ.'
      setStatus({ type: 'error', message })
    } finally {
      setDeletingId(null)
    }
  }

  const handleDownloadPackingSlip = async (order) => {
    setPdfLoading(true)
    setStatus({ type: '', message: '' })
    const rows = [
      ['Позиция', 'Кол-во'],
      ...order.items.map((item) => {
        const label = item.variant?.label ? ` (${item.variant.label})` : ''
        return [`${item.product?.name || '-'}${label}`, String(item.quantity)]
      })
    ]
    try {
      const { default: pdfMakeInstance } = await import('../pdfFonts')
      if (!pdfMakeInstance?.createPdf) {
        setStatus({ type: 'error', message: 'Не удалось загрузить модуль PDF.' })
        return
      }
      const docDefinition = {
        content: [
          { text: 'Накладная', style: 'title' },
          { text: `Заказ №${order.id} от ${formatDate(order.created_at)}`, style: 'subtitle' },
          {
            columns: [
              {
                width: '*',
                stack: [
                  { text: 'Получатель', style: 'label' },
                  { text: profile?.full_name || auth.user?.username || '-' },
                  { text: 'Клиника', style: 'label', margin: [0, 8, 0, 0] },
                  { text: profile?.clinic_name || '-' }
                ]
              },
              {
                width: '*',
                stack: [
                  { text: 'Телефон', style: 'label' },
                  { text: profile?.phone || '-' },
                  { text: 'Адрес', style: 'label', margin: [0, 8, 0, 0] },
                  { text: order.address_detail?.line1 || '-' }
                ]
              }
            ],
            columnGap: 24
          },
          {
            table: {
              headerRows: 1,
              widths: ['*', 60],
              body: rows
            },
            layout: 'lightHorizontalLines',
            margin: [0, 16, 0, 0]
          }
        ],
        styles: {
          title: { fontSize: 16, bold: true, margin: [0, 0, 0, 6] },
          subtitle: { fontSize: 10, color: '#666666', margin: [0, 0, 0, 12] },
          label: { fontSize: 9, color: '#666666' }
        },
        defaultStyle: { fontSize: 10 }
      }
      pdfMakeInstance.createPdf(docDefinition).getBlob((blob) => {
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `nakladnaya-${order.id}.pdf`
        document.body.appendChild(link)
        link.click()
        link.remove()
        URL.revokeObjectURL(url)
      })
    } catch (err) {
      setStatus({ type: 'error', message: 'Не удалось скачать PDF.' })
    } finally {
      setPdfLoading(false)
    }
  }

  const totalCount = useMemo(() => orders.length, [orders])

  if (!auth?.isAuthenticated) {
    return null
  }

  return (
    <section className="account-page">
      <div className="account-header">
        <div>
          <h2>Личный кабинет</h2>
          <p>История заказов, статусы и документы по вашим покупкам.</p>
        </div>
        <div className="account-summary">
          <span>Всего заказов</span>
          <strong>{totalCount}</strong>
        </div>
      </div>

      {status.message && (
        <div className={status.type === 'error' ? 'error' : 'success'}>{status.message}</div>
      )}

      <div className="orders-grid">
        {orders.length ? (
          orders.map((order) => (
            <article key={order.id} className="order-card">
              <div className="order-header">
                <div>
                  <h3>Заказ №{order.id}</h3>
                  <span className="muted">от {formatDate(order.created_at)}</span>
                </div>
                <div className="order-status">
                  <span className={`status-pill ${order.status}`}>
                    {statusLabels[order.status] || order.status}
                  </span>
                  {order.payment && (
                    <span className={`status-pill ${order.payment.status}`}>
                      Оплата: {paymentLabels[order.payment.status] || order.payment.status}
                    </span>
                  )}
                </div>
              </div>
              <div className="order-items">
                {order.items.map((item) => (
                  <div key={item.id} className="order-item">
                  <div className="order-item-info">
                    <strong>{item.product?.name}</strong>
                    <span className="muted">
                      {item.product?.category?.name}
                      {item.variant?.label ? ` · ${item.variant.label}` : ''}
                    </span>
                  </div>
                    <div className="order-item-meta">
                      <span>x{item.quantity}</span>
                      <span>{item.price} c.</span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="order-footer">
                <div>
                  <span className="muted">Сумма</span>
                  <strong>{order.total} c.</strong>
                </div>
                <div className="order-actions">
                  {order.status === 'pending' && (
                    <button
                      type="button"
                      className="ghost"
                      onClick={() => handleCancelOrder(order.id)}
                      disabled={cancelingId === order.id}
                    >
                      Отменить заказ
                    </button>
                  )}
                  {order.status === 'canceled' && (
                    <button
                      type="button"
                      className="ghost"
                      onClick={() => handleDeleteOrder(order.id)}
                      disabled={deletingId === order.id}
                    >
                      Удалить заказ
                    </button>
                  )}
                  <button type="button" className="ghost" onClick={() => handleReorder(order)} disabled={loading}>
                    Повторить заказ
                  </button>
                  <button type="button" className="ghost" onClick={() => setDocumentView({ type: 'invoice', order })}>
                    Счет
                  </button>
                  <button type="button" className="ghost" onClick={() => setDocumentView({ type: 'packing', order })}>
                    Накладная
                  </button>
                </div>
              </div>
            </article>
          ))
        ) : (
          <div className="panel">Пока нет заказов.</div>
        )}
      </div>

      {documentView && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal document-modal">
            <div className="modal-header">
              <h3>{documentView.type === 'invoice' ? 'Счет' : 'Накладная'}</h3>
              <button
                type="button"
                className="icon-button"
                aria-label="Закрыть"
                onClick={() => setDocumentView(null)}
              >
                ×
              </button>
            </div>
            <div className="doc-sheet printable">
              <div className="doc-head">
                <div>
                  <strong>FamilyDent TJ</strong>
                  <p className="muted">Товары и материалы для клиник</p>
                </div>
                <div className="doc-meta">
                  <span>Документ №{documentView.order.id}</span>
                  <span>Дата: {formatDate(documentView.order.created_at)}</span>
                </div>
              </div>
              <div className="doc-info">
                <div>
                  <span className="muted">Получатель</span>
                  <strong>{profile?.full_name || auth.user?.username || '-'}</strong>
                </div>
                <div>
                  <span className="muted">Клиника</span>
                  <strong>{profile?.clinic_name || '-'}</strong>
                </div>
                <div>
                  <span className="muted">Телефон</span>
                  <strong>{profile?.phone || '-'}</strong>
                </div>
                <div>
                  <span className="muted">Адрес</span>
                  <strong>{documentView.order.address_detail?.line1 || '-'}</strong>
                </div>
              </div>
              {documentView.type === 'invoice' ? (
                <div className="doc-grid">
                  <div className="doc-row head">
                    <span>Позиция</span>
                    <span>Кол-во</span>
                    <span>Цена</span>
                    <span>Сумма</span>
                  </div>
                  {documentView.order.items.map((item) => (
                    <div key={item.id} className="doc-row">
                    <span>
                      {item.product?.name}
                      {item.variant?.label ? ` (${item.variant.label})` : ''}
                    </span>
                    <span>{item.quantity}</span>
                    <span>{item.price} c.</span>
                    <span>{(Number(item.price) * item.quantity).toFixed(2)} c.</span>
                    </div>
                  ))}
                  <div className="doc-total">
                    <span>Итого</span>
                    <strong>{documentView.order.total} c.</strong>
                  </div>
                </div>
              ) : (
                <table className="doc-table">
                  <thead>
                    <tr>
                      <th>Позиция</th>
                      <th>Кол-во</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documentView.order.items.map((item) => (
                      <tr key={item.id}>
                      <td>
                        {item.product?.name}
                        {item.variant?.label ? ` (${item.variant.label})` : ''}
                      </td>
                      <td>{item.quantity}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            <div className="modal-actions">
              <button type="button" className="ghost" onClick={() => setDocumentView(null)}>
                Закрыть
              </button>
              {documentView.type === 'packing' && (
                <button
                  type="button"
                  className="ghost"
                  onClick={() => handleDownloadPackingSlip(documentView.order)}
                  disabled={pdfLoading}
                >
                  Скачать PDF
                </button>
              )}
              <button type="button" onClick={() => window.print()}>
                Печать
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
