<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

function goHome() {
  if (userStore.isLoggedIn) {
    router.push('/dashboard')
  } else {
    router.push('/login')
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#F7F8FC] to-[#EEF1FE] px-6">
    <div class="text-center max-w-md">
      <div class="text-[120px] font-bold leading-none text-[#4F6EF7] tracking-tight">404</div>
      <h1 class="text-2xl font-semibold text-gray-800 mt-2">页面找不到</h1>
      <p class="text-sm text-gray-500 mt-3">
        您访问的地址可能已被删除、链接错误，或暂时不可用。
      </p>
      <div class="mt-8 flex justify-center gap-3">
        <el-button @click="router.back()">返回上一页</el-button>
        <el-button type="primary" @click="goHome">回到首页</el-button>
      </div>
    </div>
  </div>
</template>
