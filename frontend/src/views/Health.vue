<template>
  <div style="padding: 24px">
    <h2>HRMS 健康检查</h2>
    <p>当前状态：<el-tag :type="status === 'up' ? 'success' : 'danger'">{{ status }}</el-tag></p>
    <el-button @click="check">重新检查</el-button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const status = ref<string>('未知')

async function check(): Promise<void> {
  try {
    const r = await fetch('/health')
    const body = await r.json()
    status.value = body?.data?.status || 'down'
  } catch {
    status.value = 'down'
  }
}

check()
</script>