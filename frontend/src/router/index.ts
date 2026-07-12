/**
 * 路由表 + 全局守卫
 *
 * 路由：
 *   /login         → Login.vue（公开）
 *   /              → Profile.vue（需登录）
 *   /health        → 健康检查（公开，方便本地调试）
 *
 * 守卫：
 *   已登录访问 /login → 跳首页
 *   未登录访问受保护路由 → 跳 /login
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
      meta: { public: true }
    },
    {
      path: '/',
      name: 'profile',
      component: () => import('@/views/Profile.vue')
    },
    {
      path: '/health',
      name: 'health',
      component: () => import('@/views/Health.vue'),
      meta: { public: true }
    }
  ]
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    if (to.name === 'login' && auth.accessToken) {
      return { name: 'profile' }
    }
    return true
  }
  if (!auth.accessToken) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router