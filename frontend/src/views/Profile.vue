<template>
  <div class="profile-page">
    <AppHeader />

    <el-card class="profile-card">
      <template #header>
        <h3 style="margin: 0">个人信息</h3>
      </template>

      <el-descriptions :column="1" border v-if="user">
        <el-descriptions-item label="用户 ID">{{ user.id }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ user.username }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ user.nickname || '-' }}</el-descriptions-item>
        <el-descriptions-item label="角色 ID">{{ user.role_id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="user.status === 1 ? 'success' : 'danger'">
            {{ user.status === 1 ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="最后登录时间">{{ user.login_time || '-' }}</el-descriptions-item>
        <el-descriptions-item label="最后登录 IP">{{ user.login_ip || '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-button @click="onRefresh" :loading="loading" style="margin-top: 16px">刷新</el-button>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppHeader from '@/layout/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'
import type { UserInfo } from '@/api/auth'

const auth = useAuthStore()
const user = ref<UserInfo | null>(auth.userInfo)
const loading = ref(false)

async function onRefresh(): Promise<void> {
  loading.value = true
  try {
    user.value = await auth.fetchMe()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (!auth.userInfo) {
    onRefresh()
  }
})
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: #f0f2f5;
}
.profile-card {
  max-width: 720px;
  margin: 24px auto;
}
</style>