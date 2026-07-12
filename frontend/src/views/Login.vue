<template>
  <div class="login-page">
    <el-card class="login-card">
      <template #header>
        <h2 style="margin: 0">HRMS 登录</h2>
      </template>

      <el-form :model="form" label-width="80px" @keyup.enter="onSubmit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="admin" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="admin" />
        </el-form-item>
        <el-form-item label="验证码">
          <div class="captcha-row">
            <el-input v-model="form.captcha_code" placeholder="4 位" style="flex: 1" />
            <img
              :src="captchaImage"
              class="captcha-img"
              @click="refreshCaptcha"
              title="点击刷新"
              alt="captcha"
            />
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="onSubmit" style="width: 100%">
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <el-alert
        v-if="errorMsg"
        :title="errorMsg"
        type="error"
        :closable="false"
        show-icon
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { getCaptcha, type CaptchaData } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const form = reactive({
  username: 'admin',
  password: 'admin',
  captcha_id: '',
  captcha_code: ''
})

const captchaImage = ref('')
const loading = ref(false)
const errorMsg = ref('')

async function refreshCaptcha(): Promise<void> {
  errorMsg.value = ''
  try {
    const data: CaptchaData = await getCaptcha()
    form.captcha_id = data.captcha_id
    form.captcha_code = ''
    captchaImage.value = data.captcha_image
  } catch (e: any) {
    errorMsg.value = `验证码加载失败：${e.message}`
  }
}

async function onSubmit(): Promise<void> {
  errorMsg.value = ''
  if (!form.username || !form.password || !form.captcha_code) {
    errorMsg.value = '请填写完整信息'
    return
  }
  loading.value = true
  try {
    await auth.loginAndStore({
      username: form.username,
      password: form.password,
      captcha_id: form.captcha_id,
      captcha_code: form.captcha_code
    })
    ElMessage.success('登录成功')
    const redirect = (route.query.redirect as string) || '/'
    router.replace(redirect)
  } catch (e: any) {
    errorMsg.value = e.message || '登录失败'
    refreshCaptcha()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refreshCaptcha()
})
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f0f2f5;
}
.login-card {
  width: 420px;
}
.captcha-row {
  display: flex;
  gap: 8px;
  align-items: center;
  width: 100%;
}
.captcha-img {
  height: 40px;
  cursor: pointer;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}
</style>