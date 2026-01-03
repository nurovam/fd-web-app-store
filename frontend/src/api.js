import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken'
})

export const initCsrf = () => api.get('/auth/csrf/').catch(() => {})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (!originalRequest) {
      return Promise.reject(error)
    }
    const url = originalRequest.url || ''
    const isAuthEndpoint = url.includes('/auth/token')
      || url.includes('/auth/register')
      || url.includes('/auth/logout')
      || url.includes('/auth/csrf')
    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true
      try {
        await api.post('/auth/token/refresh/')
        return api(originalRequest)
      } catch (refreshError) {
        return Promise.reject(refreshError)
      }
    }
    return Promise.reject(error)
  }
)

export default api
