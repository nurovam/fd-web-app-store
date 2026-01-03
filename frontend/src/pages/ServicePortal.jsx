import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export default function ServicePortal({ auth }) {
  const navigate = useNavigate()
  const [categories, setCategories] = useState([])
  const [products, setProducts] = useState([])
  const [categoryForm, setCategoryForm] = useState({ name: '', slug: '' })
  const [productForm, setProductForm] = useState({
    name: '',
    slug: '',
    description: '',
    price: '',
    stock_quantity: '',
    category_id: '',
    image: null
  })
  const [variants, setVariants] = useState([])
  const [variantForm, setVariantForm] = useState({
    name: '',
    color: '',
    price: '',
    stock_quantity: ''
  })
  const [variantEditingId, setVariantEditingId] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const extractList = (payload) => (Array.isArray(payload) ? payload : payload?.results || [])

  const loadCategories = () => {
    api.get('/catalog/categories/?page_size=100').then((response) => setCategories(extractList(response.data)))
  }

  const loadProducts = () => {
    api.get('/catalog/products/?page_size=100').then((response) => setProducts(extractList(response.data)))
  }

  const loadVariants = (productId) => {
    if (!productId) return
    api
      .get(`/catalog/products/${productId}/variants/`)
      .then((response) => setVariants(response.data))
      .catch(() => setVariants([]))
  }

  useEffect(() => {
    if (!auth?.isAuthenticated) {
      navigate('/login')
      return
    }
    if (auth.user && !auth.user.is_staff) {
      navigate('/catalog')
      return
    }
    if (auth.user?.is_staff) {
      loadCategories()
      loadProducts()
    }
  }, [auth, navigate])

  useEffect(() => {
    if (editingId) {
      loadVariants(editingId)
    } else {
      setVariants([])
    }
  }, [editingId])

  if (!auth?.isAuthenticated) {
    return null
  }

  if (!auth.user) {
    return (
      <section className="service">
        <div className="panel">Проверяем доступ...</div>
      </section>
    )
  }

  if (!auth.user.is_staff) {
    return null
  }

  const hasVariants = variants.length > 0

  const handleCategorySubmit = async (event) => {
    event.preventDefault()
    setMessage('')
    setError('')
    try {
      await api.post('/catalog/categories/', categoryForm)
      setMessage('Категория сохранена.')
      setCategoryForm({ name: '', slug: '' })
      loadCategories()
    } catch (err) {
      setError('Не удалось сохранить категорию. Проверьте вход сотрудника.')
    }
  }

  const resetVariantForm = () => {
    setVariantForm({
      name: '',
      color: '',
      price: '',
      stock_quantity: ''
    })
    setVariantEditingId(null)
  }

  const resetProductForm = () => {
    setProductForm({
      name: '',
      slug: '',
      description: '',
      price: '',
      stock_quantity: '',
      category_id: '',
      image: null
    })
    setEditingId(null)
    resetVariantForm()
  }

  const handleProductSubmit = async (event) => {
    event.preventDefault()
    setMessage('')
    setError('')
    try {
      const formData = new FormData()
      formData.append('name', productForm.name)
      formData.append('slug', productForm.slug)
      formData.append('description', productForm.description)
      formData.append('price', productForm.price)
      formData.append('stock_quantity', productForm.stock_quantity)
      formData.append('category_id', productForm.category_id)
      if (productForm.image) {
        formData.append('image', productForm.image)
      }
      if (editingId) {
        await api.patch(`/catalog/products/${editingId}/`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        setMessage('Карточка товара обновлена.')
      } else {
        await api.post('/catalog/products/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        setMessage('Карточка товара создана.')
      }
      resetProductForm()
      loadProducts()
    } catch (err) {
      const data = err?.response?.data
      if (data && typeof data === 'object') {
        const field = Object.keys(data)[0]
        const message = Array.isArray(data[field]) ? data[field][0] : data[field]
        setError(message || 'Не удалось сохранить товар.')
      } else {
        setError('Не удалось сохранить товар. Проверьте вход и категорию.')
      }
    }
  }

  const handleEditProduct = (product) => {
    setEditingId(product.id)
    resetVariantForm()
    setProductForm({
      name: product.name,
      slug: product.slug,
      description: product.description,
      price: product.price,
      stock_quantity: product.stock_quantity,
      category_id: product.category?.id || '',
      image: null
    })
  }

  const handleVariantSubmit = async (event) => {
    event.preventDefault()
    if (!editingId) {
      setError('Сначала выберите товар.')
      return
    }
    setMessage('')
    setError('')
    const attributes = {}
    if (variantForm.color) attributes.color = variantForm.color
    const payload = {
      name: variantForm.name,
      attributes,
      price: variantForm.price === '' ? null : variantForm.price,
      stock_quantity: variantForm.stock_quantity === '' ? 0 : variantForm.stock_quantity
    }
    try {
      if (variantEditingId) {
        await api.patch(`/catalog/variants/${variantEditingId}/`, payload)
        setMessage('Вариация обновлена.')
      } else {
        await api.post(`/catalog/products/${editingId}/variants/`, payload)
        setMessage('Вариация добавлена.')
      }
      resetVariantForm()
      loadVariants(editingId)
      loadProducts()
    } catch (err) {
      const message = err?.response?.data?.detail || 'Не удалось сохранить вариацию.'
      setError(message)
    }
  }

  const handleEditVariant = (variant) => {
    setVariantEditingId(variant.id)
    setVariantForm({
      name: variant.name || '',
      color: variant.attributes?.color || '',
      price: variant.price ?? '',
      stock_quantity: variant.stock_quantity ?? ''
    })
  }

  const handleDeleteVariant = async (variantId) => {
    setMessage('')
    setError('')
    try {
      await api.delete(`/catalog/variants/${variantId}/`)
      setMessage('Вариация удалена.')
      loadVariants(editingId)
      loadProducts()
    } catch (err) {
      const message = err?.response?.data?.detail || 'Не удалось удалить вариацию.'
      setError(message)
    }
  }

  const handleDeleteProduct = async (productId) => {
    setMessage('')
    setError('')
    try {
      await api.delete(`/catalog/products/${productId}/`)
      setMessage('Карточка товара удалена.')
      loadProducts()
      if (editingId === productId) {
        resetProductForm()
      }
    } catch (err) {
      const message = err?.response?.data?.detail || 'Не удалось удалить товар. Проверьте права доступа.'
      setError(message)
    }
  }

  return (
    <section className="service">
      <div className="service-hero">
        <h2>Рабочее место сервисного аккаунта</h2>
        <p>Используйте учетную запись сотрудника, чтобы обновлять карточки товаров.</p>
      </div>
      <div className="service-grid">
        <div className="panel">
          <h3>Новая категория</h3>
          <form onSubmit={handleCategorySubmit}>
            <label>
              Название категории
              <input
                name="name"
                value={categoryForm.name}
                onChange={(event) => setCategoryForm({ ...categoryForm, name: event.target.value })}
                required
              />
            </label>
            <label>
              Слаг
              <input
                name="slug"
                value={categoryForm.slug}
                onChange={(event) => setCategoryForm({ ...categoryForm, slug: event.target.value })}
                required
              />
            </label>
            <button type="submit">Сохранить категорию</button>
          </form>
        </div>
        <div className="panel">
          <h3>{editingId ? 'Редактирование товара' : 'Новая карточка товара'}</h3>
          <form onSubmit={handleProductSubmit}>
            <label>
              Название товара
              <input
                name="name"
                value={productForm.name}
                onChange={(event) => setProductForm({ ...productForm, name: event.target.value })}
                required
              />
            </label>
            <label>
              Слаг
              <input
                name="slug"
                value={productForm.slug}
                onChange={(event) => setProductForm({ ...productForm, slug: event.target.value })}
                required
              />
            </label>
            <label>
              Описание
              <textarea
                name="description"
                value={productForm.description}
                onChange={(event) => setProductForm({ ...productForm, description: event.target.value })}
                required
              />
            </label>
            <label>
              Цена (сомони)
              <input
                name="price"
                type="number"
                step="0.01"
                value={productForm.price}
                onChange={(event) => setProductForm({ ...productForm, price: event.target.value })}
                required
              />
            </label>
            <label>
              Количество в наличии
              <input
                name="stock_quantity"
                type="number"
                min="0"
                value={productForm.stock_quantity}
                onChange={(event) => setProductForm({ ...productForm, stock_quantity: event.target.value })}
                required
                disabled={editingId && hasVariants}
              />
            </label>
            {editingId && hasVariants && (
              <div className="muted">Остаток управляется через вариации.</div>
            )}
            <label>
              Категория
              <select
                name="category_id"
                value={productForm.category_id}
                onChange={(event) => setProductForm({ ...productForm, category_id: event.target.value })}
                required
              >
                <option value="">Выберите</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Изображение
              <input
                name="image"
                type="file"
                accept="image/*"
                onChange={(event) => setProductForm({ ...productForm, image: event.target.files[0] })}
              />
            </label>
            <button type="submit">{editingId ? 'Сохранить изменения' : 'Создать товар'}</button>
            {editingId && (
              <button type="button" className="ghost" onClick={resetProductForm}>
                Отменить
              </button>
            )}
          </form>
        </div>
        {editingId && (
          <div className="panel">
            <h3>Вариации товара</h3>
            <form onSubmit={handleVariantSubmit}>
              <label>
                Название варианта
                <input
                  name="variantName"
                  value={variantForm.name}
                  onChange={(event) => setVariantForm({ ...variantForm, name: event.target.value })}
                  placeholder="Например: XL или Классик"
                />
              </label>
              <label>
                Цвет (опционально)
                <input
                  name="color"
                  value={variantForm.color}
                  onChange={(event) => setVariantForm({ ...variantForm, color: event.target.value })}
                  placeholder="Синий"
                />
              </label>
              <label>
                Цена (сомони)
                <input
                  name="price"
                  type="number"
                  step="0.01"
                  value={variantForm.price}
                  onChange={(event) => setVariantForm({ ...variantForm, price: event.target.value })}
                />
              </label>
              <label>
                Количество в наличии
                <input
                  name="variantStock"
                  type="number"
                  min="0"
                  value={variantForm.stock_quantity}
                  onChange={(event) => setVariantForm({ ...variantForm, stock_quantity: event.target.value })}
                  required
                />
              </label>
              <button type="submit">{variantEditingId ? 'Сохранить вариацию' : 'Добавить вариацию'}</button>
              {variantEditingId && (
                <button type="button" className="ghost" onClick={resetVariantForm}>
                  Отменить
                </button>
              )}
            </form>
            <div className="service-list">
              {variants.length ? (
                variants.map((variant) => (
                  <div key={variant.id} className="service-item">
                    <div>
                      <strong>{variant.label || variant.name || 'Вариант'}</strong>
                      <div className="muted">
                        Остаток: {variant.stock_quantity}
                        {variant.price !== null && variant.price !== undefined ? ` · ${variant.price} c.` : ''}
                      </div>
                    </div>
                    <div className="service-actions">
                      <button type="button" className="ghost" onClick={() => handleEditVariant(variant)}>
                        Редактировать
                      </button>
                      <button type="button" className="ghost" onClick={() => handleDeleteVariant(variant.id)}>
                        Удалить
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="muted">Добавьте первую вариацию товара.</div>
              )}
            </div>
          </div>
        )}
        <div className="panel">
          <h3>Каталог товаров</h3>
          <div className="service-list">
            {products.map((product) => (
              <div key={product.id} className="service-item">
                <div>
                  <strong>{product.name}</strong>
                  <div className="muted">
                    {product.category?.name} · Остаток: {product.stock_quantity}
                  </div>
                </div>
                <div className="service-actions">
                  <button
                    type="button"
                    className="icon-button"
                    aria-label="Редактировать товар"
                    onClick={() => handleEditProduct(product)}
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path
                        d="M3 17.25V21h3.75l11-11-3.75-3.75-11 11zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"
                        fill="currentColor"
                      />
                    </svg>
                  </button>
                  <button
                    type="button"
                    className="icon-button danger"
                    aria-label="Удалить товар"
                    onClick={() => handleDeleteProduct(product.id)}
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path
                        d="M6 7h12l-1 14H7L6 7zm3-3h6l1 2H8l1-2z"
                        fill="currentColor"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      {message && <div className="success">{message}</div>}
      {error && <div className="error">{error}</div>}
    </section>
  )
}
