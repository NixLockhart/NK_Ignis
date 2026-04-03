<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({ username: '', password: '' })

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await userStore.login(form)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch { /* 错误已在拦截器中处理 */ } finally { loading.value = false }
}
</script>

<template>
  <div class="min-h-screen flex">
    <!-- 左侧插画区 -->
    <div class="hidden lg:flex lg:w-[58%] bg-gradient-to-br from-[#4F6EF7] via-[#6C8CFA] to-[#36CFC9] items-center justify-center relative overflow-hidden">
      <!-- 装饰圆 -->
      <div class="absolute -top-20 -left-20 w-80 h-80 bg-white/10 rounded-full"></div>
      <div class="absolute -bottom-32 -right-32 w-96 h-96 bg-white/5 rounded-full"></div>
      <div class="absolute top-1/4 right-10 w-40 h-40 bg-white/5 rounded-full"></div>
      <!-- 文案 -->
      <div class="relative z-10 text-center text-white px-12">
        <div class="text-5xl mb-6">🏫</div>
        <h1 class="text-3xl font-bold mb-4">高校青年志愿者服务</h1>
        <h2 class="text-xl font-light mb-6 opacity-90">AI 智能管理系统</h2>
        <p class="text-sm opacity-70 max-w-sm mx-auto leading-relaxed">
          志愿服务全流程数字化管理，AI赋能项目推荐与数据分析，让每一份奉献都被记录
        </p>
        <div class="flex justify-center gap-8 mt-10 text-sm opacity-80">
          <div class="text-center">
            <div class="text-2xl font-bold">50+</div>
            <div class="opacity-70">志愿项目</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold">300+</div>
            <div class="opacity-70">服务记录</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold">AI</div>
            <div class="opacity-70">智能推荐</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="flex-1 flex items-center justify-center bg-[#F7F8FC] px-6">
      <div class="w-full max-w-sm">
        <!-- Logo（移动端显示） -->
        <div class="text-center mb-8">
          <div class="lg:hidden text-4xl mb-3">🏫</div>
          <h2 class="text-2xl font-bold text-gray-800">欢迎回来</h2>
          <p class="text-sm text-gray-400 mt-2">登录您的账号以继续</p>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" size="large">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password :prefix-icon="Lock" @keyup.enter="handleLogin" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" class="w-full !h-11 !text-base !rounded-lg" :loading="loading" @click="handleLogin">登 录</el-button>
          </el-form-item>
        </el-form>

        <div class="text-center text-sm text-gray-400 mt-4">
          还没有账号？<router-link to="/register" class="text-[#4F6EF7] font-medium hover:underline">立即注册</router-link>
        </div>
      </div>
    </div>
  </div>
</template>
