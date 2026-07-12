<template>
  <header class="app-header">
    <div class="title">HRMS</div>
    <div class="user-area">
      <span class="username" v-if="auth.userInfo">{{ auth.userInfo.username }}</span>
      <el-button type="danger" size="small" @click="onLogout">登出</el-button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function onLogout(): Promise<void> {
  await auth.logoutAndClear()
  ElMessage.success('已登出')
  router.replace('/login')
}
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  background: #001529;
  color: #fff;
}
.title {
  font-size: 18px;
  font-weight: 600;
}
.user-area {
  display: flex;
  align-items: center;
  gap: 12px;
}
.username {
  color: #fff;
}
</style>