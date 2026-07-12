/**
 * 认证状态 Pinia store
 *
 * 状态：
 *   - accessToken / refreshToken：登录凭证
 *   - userInfo：当前用户
 *
 * 持久化：使用 localStorage（key: hrms-auth），刷新页面不丢失登录态
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { LoginIn, LoginOut, UserInfo } from '@/api/auth'
import { login as apiLogin, logout as apiLogout, me as apiMe } from '@/api/auth'

const STORAGE_KEY = 'hrms-auth'

interface PersistedState {
  accessToken: string
  refreshToken: string
  userInfo: UserInfo | null
}

function loadFromStorage(): PersistedState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { accessToken: '', refreshToken: '', userInfo: null }
    return JSON.parse(raw)
  } catch {
    return { accessToken: '', refreshToken: '', userInfo: null }
  }
}

function saveToStorage(state: PersistedState): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

function clearStorage(): void {
  localStorage.removeItem(STORAGE_KEY)
}

export const useAuthStore = defineStore('auth', () => {
  const initial = loadFromStorage()
  const accessToken = ref<string>(initial.accessToken)
  const refreshToken = ref<string>(initial.refreshToken)
  const userInfo = ref<UserInfo | null>(initial.userInfo)

  function persist(): void {
    saveToStorage({
      accessToken: accessToken.value,
      refreshToken: refreshToken.value,
      userInfo: userInfo.value
    })
  }

  function setTokens(access: string, refresh: string): void {
    accessToken.value = access
    refreshToken.value = refresh
    persist()
  }

  function setUser(info: UserInfo): void {
    userInfo.value = info
    persist()
  }

  async function loginAndStore(payload: LoginIn): Promise<LoginOut> {
    const out = await apiLogin(payload)
    accessToken.value = out.access_token
    refreshToken.value = out.refresh_token
    userInfo.value = out.user
    persist()
    return out
  }

  async function fetchMe(): Promise<UserInfo> {
    const info = await apiMe()
    userInfo.value = info
    persist()
    return info
  }

  async function logoutAndClear(): Promise<void> {
    try {
      await apiLogout()
    } catch {
      // 忽略登出错误（可能 token 已过期）
    }
    clear()
  }

  function clear(): void {
    accessToken.value = ''
    refreshToken.value = ''
    userInfo.value = null
    clearStorage()
  }

  return {
    accessToken,
    refreshToken,
    userInfo,
    setTokens,
    setUser,
    loginAndStore,
    fetchMe,
    logoutAndClear,
    clear
  }
})