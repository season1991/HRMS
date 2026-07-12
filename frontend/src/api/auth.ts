/**
 * 认证模块接口封装（按 backend/spec/openapi_auth.json 契约生成）
 *
 * 5 个接口：
 *   - getCaptcha()
 *   - login(payload)
 *   - logout()
 *   - refresh(refreshToken)
 *   - me()
 */
import { http } from '@/utils/request'

export interface CaptchaData {
  captcha_id: string
  captcha_code: string
  captcha_image: string
}

export interface LoginIn {
  username: string
  password: string
  captcha_id: string
  captcha_code: string
}

export interface UserInfo {
  id: number
  username: string
  nickname: string | null
  role_id: number
  status: number
  login_time: string | null
  login_ip: string | null
}

export interface LoginOut {
  access_token: string
  refresh_token: string
  token_type: string
  user: UserInfo
}

export interface RefreshIn {
  refresh_token: string
}

export interface RefreshOut {
  access_token: string
  refresh_token: string
  token_type: string
}

/** GET /api/auth/captcha */
export function getCaptcha(): Promise<CaptchaData> {
  return http.get('/api/auth/captcha').then((r: any) => r.data)
}

/** POST /api/auth/login */
export function login(payload: LoginIn): Promise<LoginOut> {
  return http.post('/api/auth/login', payload).then((r: any) => r.data)
}

/** POST /api/auth/logout（需 Bearer Token） */
export function logout(): Promise<null> {
  return http.post('/api/auth/logout').then((r: any) => r.data)
}

/** POST /api/auth/refresh */
export function refresh(refreshToken: string): Promise<RefreshOut> {
  return http.post('/api/auth/refresh', { refresh_token: refreshToken }).then((r: any) => r.data)
}

/** GET /api/auth/me（需 Bearer Token） */
export function me(): Promise<UserInfo> {
  return http.get('/api/auth/me').then((r: any) => r.data)
}