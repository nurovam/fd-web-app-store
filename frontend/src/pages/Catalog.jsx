import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export default function Catalog({ auth }) {
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [filters, setFilters] = useState({
    search: '',
    category: '',
    minPrice: '',
    maxPrice: '',
    availableOnly: false
  })
  const [searchInput, setSearchInput] = useState('')
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [loadingProducts, setLoadingProducts] = useState(false)
  const [loadingCategories, setLoadingCategories] = useState(false)
  const [downloadingPriceList, setDownloadingPriceList] = useState(false)
  const [cartItems, setCartItems] = useState({})
  const [selectedVariants, setSelectedVariants] = useState({})
  const [variantSelections, setVariantSelections] = useState({})
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [consultationOpen, setConsultationOpen] = useState(false)
  const [consultationForm, setConsultationForm] = useState({ name: '', phone: '', message: '' })
  const [consultationStatus, setConsultationStatus] = useState({ type: '', message: '' })
  const [consultationLoading, setConsultationLoading] = useState(false)
  const navigate = useNavigate()

  const itemKey = (productId, variantId) => (variantId ? `v-${variantId}` : `p-${productId}`)
  const colorMap = {
    белый: '#ffffff',
    черный: '#111111',
    серый: '#9aa0a6',
    синий: '#2f6fed',
    голубой: '#7bb6ff',
    зеленый: '#3c9b59',
    красный: '#d64545',
    розовый: '#f1a7c7',
    фиолетовый: '#7c5cb8',
    желтый: '#f2c94c',
    оранжевый: '#f2994a',
    бежевый: '#e6d5c3',
    коричневый: '#8b6b4f'
  }

  const resolveColor = (value) => {
    if (!value) return '#dcd6cc'
    const normalized = value.trim().toLowerCase()
    if (normalized.startsWith('#') || normalized.startsWith('rgb')) {
      return value
    }
    return colorMap[normalized] || '#dcd6cc'
  }

  const extractList = (payload) => (Array.isArray(payload) ? payload : payload?.results || [])
  const pageSize = 24

  const buildProductQuery = (pageValue) => {
    const params = new URLSearchParams()
    params.set('page', pageValue)
    params.set('page_size', pageSize)
    if (filters.search) params.set('search', filters.search)
    if (filters.category) params.set('category', filters.category)
    if (filters.minPrice) params.set('min_price', filters.minPrice)
    if (filters.maxPrice) params.set('max_price', filters.maxPrice)
    if (filters.availableOnly) params.set('is_available', 'true')
    return params.toString()
  }

  const loadProducts = async (pageValue, replace = false) => {
    setLoadingProducts(true)
    setError('')
    try {
      const response = await api.get(`/catalog/products/?${buildProductQuery(pageValue)}`)
      const list = extractList(response.data)
      setProducts((prev) => (replace ? list : [...prev, ...list]))
      const hasNext = Array.isArray(response.data) ? list.length === pageSize : Boolean(response.data?.next)
      setHasMore(hasNext)
      setPage(pageValue)
    } catch (err) {
      setError('Не удалось загрузить каталог.')
    } finally {
      setLoadingProducts(false)
    }
  }

  const resetFilters = () => {
    setSearchInput('')
    setFilters({
      search: '',
      category: '',
      minPrice: '',
      maxPrice: '',
      availableOnly: false
    })
  }

  const downloadPriceList = async () => {
    setError('')
    setMessage('')
    setDownloadingPriceList(true)
    try {
      const response = await api.get('/catalog/pricelist/', { responseType: 'blob' })
      const contentDisposition = response.headers['content-disposition'] || ''
      const match = contentDisposition.match(/filename="?([^"]+)"?/i)
      const filename = match?.[1] || 'pricelist.pdf'
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      setMessage('Прайс-лист скачан.')
    } catch (err) {
      setError('Не удалось скачать прайс-лист.')
    } finally {
      setDownloadingPriceList(false)
    }
  }

  const openConsultation = () => {
    setConsultationStatus({ type: '', message: '' })
    setConsultationOpen(true)
  }

  const closeConsultation = () => {
    setConsultationOpen(false)
  }

  const handleConsultationChange = (event) => {
    const { name, value } = event.target
    setConsultationForm((prev) => ({ ...prev, [name]: value }))
  }

  const submitConsultation = async (event) => {
    event.preventDefault()
    const name = consultationForm.name.trim()
    const phone = consultationForm.phone.trim()
    const messageText = consultationForm.message.trim()
    if (!name || !phone) {
      setConsultationStatus({ type: 'error', message: 'Укажите имя и телефон.' })
      return
    }
    setConsultationLoading(true)
    setConsultationStatus({ type: '', message: '' })
    try {
      await api.post('/consultation/', {
        name,
        phone,
        message: messageText,
        page_url: window.location.href
      })
      setConsultationStatus({ type: 'success', message: 'Запрос отправлен! Мы скоро свяжемся.' })
      setConsultationForm({ name: '', phone: '', message: '' })
      setConsultationOpen(false)
    } catch (err) {
      const message = err?.response?.data?.detail || 'Не удалось отправить запрос.'
      setConsultationStatus({ type: 'error', message })
    } finally {
      setConsultationLoading(false)
    }
  }

  useEffect(() => {
    let isMounted = true
    setLoadingCategories(true)
    api
      .get('/catalog/categories/?page_size=200')
      .then((response) => {
        if (isMounted) {
          setCategories(extractList(response.data))
        }
      })
      .catch(() => {
        if (isMounted) {
          setCategories([])
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoadingCategories(false)
        }
      })
    return () => {
      isMounted = false
    }
  }, [])

  useEffect(() => {
    const timeout = setTimeout(() => {
      const nextSearch = searchInput.trim()
      setFilters((prev) => (prev.search === nextSearch ? prev : { ...prev, search: nextSearch }))
    }, 400)
    return () => clearTimeout(timeout)
  }, [searchInput])

  useEffect(() => {
    loadProducts(1, true)
  }, [filters])

  const getVariantOptionMeta = (product) => {
    const variants = product.variants || []
    const hasNameOptions = variants.some((variant) => (variant.name || '').trim())
    const hasColorOptions = variants.some((variant) => variant.attributes?.color)
    const labelOnlyMode = !hasNameOptions && !hasColorOptions
    return { hasNameOptions, hasColorOptions, labelOnlyMode }
  }

  const findVariantMatch = (product, selection, optionMeta) => {
    const { hasNameOptions, hasColorOptions, labelOnlyMode } = optionMeta
    return (product.variants || []).find((variant) => {
      const nameMatch = labelOnlyMode
        ? (selection.name ? (variant.label || variant.name) === selection.name : true)
        : (hasNameOptions && selection.name ? variant.name === selection.name : true)
      const colorMatch = hasColorOptions && selection.color
        ? variant.attributes?.color === selection.color
        : true
      return nameMatch && colorMatch
    })
  }

  useEffect(() => {
    if (!products.length) return
    setVariantSelections((prev) => {
      const next = { ...prev }
      const nextVariants = {}
      products.forEach((product) => {
        if (!product.variants?.length) return
        const optionMeta = getVariantOptionMeta(product)
        const currentVariantId = selectedVariants[product.id]
        const exists = product.variants.some((variant) => variant.id === currentVariantId)
        if (!next[product.id] || !exists) {
          const available = product.variants.find((variant) => variant.is_available)
          const fallback = available || product.variants[0]
          if (fallback) {
            next[product.id] = {
              name: optionMeta.labelOnlyMode ? (fallback.label || fallback.name || '') : (fallback.name || ''),
              color: optionMeta.hasColorOptions ? (fallback.attributes?.color || '') : ''
            }
            nextVariants[product.id] = fallback.id
          }
        }
      })
      if (Object.keys(nextVariants).length) {
        setSelectedVariants((prevSelected) => ({ ...prevSelected, ...nextVariants }))
      }
      return next
    })
  }, [products, selectedVariants])

  useEffect(() => {
    if (!auth?.isAuthenticated) {
      setCartItems({})
      return
    }
    loadCart()
  }, [auth])

  const loadCart = () => {
    api
      .get('/cart/')
      .then((response) => {
        const nextItems = {}
        response.data.items.forEach((item) => {
          if (item.product?.id) {
            const key = itemKey(item.product.id, item.variant?.id)
            nextItems[key] = { id: item.id, quantity: item.quantity }
          }
        })
        setCartItems(nextItems)
      })
      .catch(() => {
        setCartItems({})
      })
  }

  const handleAddToCart = async (productId, variantId, hasVariants) => {
    setMessage('')
    setError('')
    if (!auth?.isAuthenticated) {
      navigate('/login')
      return
    }
    if (hasVariants && !variantId) {
      setError('Выберите вариант.')
      return
    }
    try {
      await api.post('/cart/', { product_id: productId, variant_id: variantId || null, quantity: 1 })
      loadCart()
      setMessage('Товар добавлен в корзину.')
    } catch (err) {
      if (err?.response?.status === 401) {
        navigate('/login')
        return
      }
      const message = err?.response?.data?.detail || 'Не удалось добавить товар.'
      setError(message)
    }
  }

  const updateCartItem = async (itemId, quantity) => {
    setMessage('')
    setError('')
    try {
      if (quantity < 1) {
        await api.delete(`/cart/items/${itemId}/`)
      } else {
        await api.patch(`/cart/items/${itemId}/`, { quantity })
      }
      loadCart()
    } catch (err) {
      setError('Не удалось обновить корзину.')
    }
  }

  const updateVariantSelection = (product, updates) => {
    const current = variantSelections[product.id] || { name: '', color: '' }
    const nextSelection = { ...current, ...updates }
    const optionMeta = getVariantOptionMeta(product)
    let match = findVariantMatch(product, nextSelection, optionMeta)
    if (!match && Object.keys(updates).length) {
      const relaxed = { name: '', color: '', ...updates }
      match = findVariantMatch(product, relaxed, optionMeta)
    }
    if (match) {
      const syncedSelection = {
        name: optionMeta.labelOnlyMode
          ? (match.label || match.name || '')
          : (optionMeta.hasNameOptions ? (match.name || '') : ''),
        color: optionMeta.hasColorOptions ? (match.attributes?.color || '') : ''
      }
      setVariantSelections((prev) => ({ ...prev, [product.id]: syncedSelection }))
      setSelectedVariants((prev) => ({ ...prev, [product.id]: match.id }))
      return
    }
    setVariantSelections((prev) => ({ ...prev, [product.id]: nextSelection }))
    setSelectedVariants((prev) => ({ ...prev, [product.id]: null }))
  }

  return (
    <section className="catalog">
      <div className="hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">FamilyDent · Клинические поставки</p>
          <h2>Соберите кабинет, которому доверяют пациенты</h2>
          <p>
            Каталог стерильных наборов, диагностических систем и расходных материалов.
            Отгружаем со склада в Душанбе и поддерживаем закупки клиник.
          </p>
          <div className="hero-actions">
            <button type="button" onClick={openConsultation}>Запросить консультацию</button>
            <button type="button" className="ghost" onClick={downloadPriceList} disabled={downloadingPriceList}>
              {downloadingPriceList ? 'Скачиваем...' : 'Скачать прайс-лист'}
            </button>
          </div>
          <div className="hero-stats">
            <div>
              <strong>120+</strong>
              <span>позиций в наличии</span>
            </div>
            <div>
              <strong>24 ч</strong>
              <span>среднее время отгрузки</span>
            </div>
          </div>
        </div>
        <div className="hero-card">
          <h3>Наборы для клиник</h3>
          <p>Комплектуем под протоколы лечения: терапия, хирургия, ортодонтия.</p>
          <div className="hero-card-list">
            <span>Подбор расходников</span>
            <span>Сервисное сопровождение</span>
            <span>Техническая поддержка</span>
          </div>
          <div className="hero-card-footer">
            <span>Склад: Душанбе, ул. С. Шерози</span>
            <span>Горячая линия</span>
          </div>
        </div>
      </div>
      <div className="filters-panel">
        <div className="filters-row">
          <label className="filter-field">
            <span>Поиск</span>
            <input
              className="filter-input"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Название или описание"
            />
          </label>
          <label className="filter-field">
            <span>Цена от</span>
            <input
              className="filter-input"
              type="number"
              min="0"
              value={filters.minPrice}
              onChange={(event) => setFilters((prev) => ({ ...prev, minPrice: event.target.value }))}
            />
          </label>
          <label className="filter-field">
            <span>Цена до</span>
            <input
              className="filter-input"
              type="number"
              min="0"
              value={filters.maxPrice}
              onChange={(event) => setFilters((prev) => ({ ...prev, maxPrice: event.target.value }))}
            />
          </label>
          <label className="filter-toggle">
            <input
              type="checkbox"
              checked={filters.availableOnly}
              onChange={(event) => setFilters((prev) => ({ ...prev, availableOnly: event.target.checked }))}
            />
            Только в наличии
          </label>
          <button type="button" className="ghost" onClick={resetFilters}>
            Сбросить
          </button>
        </div>
        <div className="filters-row">
          <button
            type="button"
            className={`chip ${filters.category ? '' : 'active'}`}
            onClick={() => setFilters((prev) => ({ ...prev, category: '' }))}
          >
            Все
          </button>
          {categories.map((category) => {
            const value = String(category.id)
            return (
              <button
                key={category.id}
                type="button"
                className={`chip ${filters.category === value ? 'active' : ''}`}
                onClick={() => setFilters((prev) => ({ ...prev, category: value }))}
              >
                {category.name}
              </button>
            )
          })}
        </div>
        {loadingCategories && <div className="muted">Загружаем категории...</div>}
      </div>
      <div className="product-grid">
        {products.map((product) => {
          const variants = product.variants || []
          const optionMeta = getVariantOptionMeta(product)
          const selectedVariantId = selectedVariants[product.id]
          const selectedVariant = variants.find((variant) => variant.id === selectedVariantId)
          const selection = variantSelections[product.id] || { name: '', color: '' }
          const nameOptions = optionMeta.hasNameOptions
            ? [...new Set(variants.map((variant) => variant.name).filter(Boolean))]
            : (optionMeta.labelOnlyMode
              ? [...new Set(variants.map((variant) => variant.label).filter(Boolean))]
              : [])
          const colorSource = optionMeta.hasColorOptions
            ? (optionMeta.hasNameOptions && selection.name
              ? variants.filter((variant) => variant.name === selection.name)
              : variants)
            : []
          const colorOptions = optionMeta.hasColorOptions
            ? [...new Set(colorSource.map((variant) => variant.attributes?.color).filter(Boolean))]
            : []
          const hasVariants = variants.length > 0
          const priceValue = selectedVariant?.price ?? product.price
          const isNameOptionAvailable = (option) => {
            const candidates = optionMeta.labelOnlyMode
              ? variants.filter((variant) => (variant.label || variant.name) === option)
              : variants.filter((variant) => variant.name === option)
            return candidates.some((variant) => variant.is_available)
          }
          return (
            <article key={product.id} className="product-card">
            <div className="card-media">
              {product.image_url ? (
                <img src={product.image_url} alt={product.name} />
              ) : (
                <div className="placeholder">Нет изображения</div>
              )}
            </div>
            <div className="card-body">
              <div className="card-top">
                <h3>{product.name}</h3>
                <span className="price">{priceValue} c.</span>
              </div>
              <p>{product.description}</p>
              {hasVariants ? (
                <div className="variant-options">
                  {nameOptions.length > 0 && (
                    <div className="option-group">
                      <span className="option-label">Вариант</span>
                      <div className="option-list">
                        {nameOptions.map((option) => {
                          const isAvailable = isNameOptionAvailable(option)
                          return (
                          <button
                            key={option}
                            type="button"
                            className={`option-button ${selection.name === option ? 'active' : ''}`}
                            onClick={() => updateVariantSelection(product, { name: option })}
                            disabled={!isAvailable}
                          >
                            {option}
                          </button>
                          )
                        })}
                      </div>
                    </div>
                  )}
                  {colorOptions.length > 0 && (
                    <div className="option-group">
                      <span className="option-label">Цвет</span>
                      <div className="color-options">
                        {colorOptions.map((option) => (
                          <button
                            key={option}
                            type="button"
                            className={`color-swatch ${selection.color === option ? 'active' : ''}`}
                            style={{ backgroundColor: resolveColor(option) }}
                            title={option}
                            aria-label={`Цвет ${option}`}
                            onClick={() => updateVariantSelection(product, { color: option })}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : null}
              <div className="card-meta">
                <span>{product.category?.name}</span>
                <span>
                  {hasVariants
                    ? (selectedVariant
                      ? (selectedVariant.stock_quantity > 0
                        ? `В наличии: ${selectedVariant.stock_quantity}`
                        : 'Под заказ')
                      : 'Выберите вариант')
                    : (product.stock_quantity > 0
                      ? `В наличии: ${product.stock_quantity}`
                      : 'Под заказ')}
                </span>
              </div>
              {(() => {
                const key = itemKey(product.id, selectedVariantId)
                const cartItem = cartItems[key]
                if (!cartItem) {
                  return (
                    <button
                      type="button"
                      onClick={() => handleAddToCart(product.id, selectedVariantId, hasVariants)}
                      disabled={hasVariants && !selectedVariantId}
                    >
                      В корзину
                    </button>
                  )
                }
                return (
                  <div className="qty-controls">
                    <button
                      type="button"
                      className="ghost"
                      onClick={() => updateCartItem(cartItem.id, cartItem.quantity - 1)}
                    >
                      −
                    </button>
                    <span>{cartItem.quantity}</span>
                    <button
                      type="button"
                      className="ghost"
                      onClick={() => updateCartItem(cartItem.id, cartItem.quantity + 1)}
                    >
                      +
                    </button>
                  </div>
                )
              })()}
            </div>
          </article>
          )
        })}
      </div>
      {loadingProducts && !products.length && <div className="panel">Загружаем товары...</div>}
      {hasMore && products.length > 0 && (
        <div className="load-more">
          <button type="button" onClick={() => loadProducts(page + 1)} disabled={loadingProducts}>
            {loadingProducts ? 'Загружаем...' : 'Показать еще'}
          </button>
        </div>
      )}
      {!hasMore && products.length > 0 && <div className="muted">Это все товары по выбранным фильтрам.</div>}
      {consultationOpen && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal">
            <div className="modal-header">
              <h3>Запрос консультации</h3>
              <button type="button" className="icon-button" aria-label="Закрыть" onClick={closeConsultation}>
                ×
              </button>
            </div>
            <form className="modal-body" onSubmit={submitConsultation}>
              <label>
                Имя
                <input
                  name="name"
                  value={consultationForm.name}
                  onChange={handleConsultationChange}
                  required
                />
              </label>
              <label>
                Телефон
                <input
                  name="phone"
                  value={consultationForm.phone}
                  onChange={handleConsultationChange}
                  required
                />
              </label>
              <label>
                Комментарий
                <textarea
                  name="message"
                  value={consultationForm.message}
                  onChange={handleConsultationChange}
                  rows="3"
                />
              </label>
              {consultationStatus.message && (
                <div className={consultationStatus.type === 'error' ? 'error' : 'success'}>
                  {consultationStatus.message}
                </div>
              )}
              <div className="modal-actions">
                <button type="button" className="ghost" onClick={closeConsultation}>
                  Отмена
                </button>
                <button type="submit" disabled={consultationLoading}>
                  {consultationLoading ? 'Отправляем...' : 'Отправить'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {message && <div className="success">{message}</div>}
      {error && <div className="error">{error}</div>}
      {consultationStatus.message && !consultationOpen && (
        <div className={consultationStatus.type === 'error' ? 'error' : 'success'}>
          {consultationStatus.message}
        </div>
      )}
    </section>
  )
}
