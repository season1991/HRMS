/**
 * Axios 实例 + 拦截器
 *
 * - 请求拦截器：从 Pinia auth store 取 access_token 注入 Authorization 头
 * - 响应拦截器：
 *   - 业务码 200 → 直接返回 data
 *   - 业务码 401（access 失效）→ 尝试用 refresh_token 刷新，重放原请求
 *   - 业务码 401（refresh 也失效）→ 清空 store + 跳登录页
 *   - 其他错误 → 统一抛异常让上层处理
 */
import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

export const http: AxiosInstance = axios.create({
  baseURL: '/',
  timeout: 10000
})

http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.set('Authorization', `Bearer ${auth.accessToken}`)
  }
  return config
})

let isRefreshing = false
let pendingQueue: Array<(token: string | null) => void> = []

http.interceptors.response.use(
  (response) => {
    const body = response.data
    // 业务码 200 直接放行
    if (body && body.code === 200) {
      return body
    }
    // 业务码 401：尝试刷新
    if (body && body.code === 401) {
      return handleUnauthorized(response)
    }
    // 其他业务码：弹错误
    return Promise.reject(new Error(body?.message || '请求失败'))
  },
  (error) => {
    // HTTP 层面的 401（无 body）也走刷新流程
    if (error.response?.status === 401) {
      return handleUnauthorized(error.response)
    }
    return Promise.reject(error)
  }
)

async function handleUnauthorized(response: any): Promise<any> {
  const auth = useAuthStore()

  // 没有 refresh_token，直接跳登录
  if (!auth.refreshToken) {
    auth.clear()
    router.replace('/login')
    return Promise.reject(new Error('未登录'))
  }

  // 已经有刷新在进行，把请求排入队列
  if (isRefreshing) {
    return new Promise((resolve) => {
      pendingQueue.push((newToken) => {
        if (newToken) {
          response.config.headers.Authorization = `Bearer ${newToken}`
          resolve(http(response.config))
        } else {
          resolve(Promise.reject(new Error('刷新失败')))
        }
      })
    })
  }

  isRefreshing = true
  try {
    const resp = await axios.post(
      '/api/auth/refresh',
      { refresh_token: auth.refreshToken }
    )
    const data = resp.data?.data
    if (resp.data?.code !== 200 || !data?.access_token || !data?.refresh_token) {
      throw new Error('refresh 响应异常')
    }
    auth.setTokens(data.access_token, data.refresh_token)
    pendingQueue.forEach((cb) => cb(data.access_token))
    pendingQueue = []
    response.config.headers.Authorization = `Bearer ${data.access_token}`
    return http(response.config)
  } catch (e) {
    pendingQueue.forEach((cb) => cb(null))
    pendingQueue = []
    auth.clear()
    router.replace('/login')
    return Promise.reject(e)
  } finally {
    isRefreshing = false
  }
}