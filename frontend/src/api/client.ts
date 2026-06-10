import axios from 'axios'
import type { InternalAxiosRequestConfig } from 'axios'

const apiClient = axios.create({
  baseURL: '/',
  withCredentials: true,
})

apiClient.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const { useAuthStore } = await import('@/stores/auth')
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401) {
      const { useAuthStore } = await import('@/stores/auth')
      useAuthStore().logout()
      const { default: router } = await import('@/router')
      router.push('/login')
    }
    return Promise.reject(err)
  },
)

export default apiClient
