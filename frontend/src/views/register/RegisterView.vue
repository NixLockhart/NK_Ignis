<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { registerApi, type RegisterParams } from '@/api/auth'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive<RegisterParams & { confirmPassword: string }>({
  username: '',
  password: '',
  confirmPassword: '',
  realName: '',
  studentId: '',
  college: '',
  major: '',
  phone: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  realName: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  studentId: [
    { required: true, message: '请输入学号', trigger: 'blur' },
    { pattern: /^\d{6,12}$/, message: '学号为 6-12 位数字', trigger: 'blur' },
  ],
  college: [{ required: true, message: '请输入学院', trigger: 'blur' }],
  major: [{ required: true, message: '请输入专业', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
}

async function handleRegister() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const { confirmPassword: _, ...params } = form
    await registerApi(params)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-center min-h-screen bg-gray-100 py-8">
    <el-card class="w-[480px]" shadow="hover">
      <template #header>
        <div class="text-center">
          <h2 class="text-xl font-bold text-gray-800 m-0">注册新账号</h2>
          <p class="text-sm text-gray-500 mt-1">填写以下信息完成注册</p>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>

        <div class="flex gap-3">
          <el-form-item label="密码" prop="password" class="flex-1">
            <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword" class="flex-1">
            <el-input v-model="form.confirmPassword" type="password" placeholder="请确认密码" show-password />
          </el-form-item>
        </div>

        <div class="flex gap-3">
          <el-form-item label="真实姓名" prop="realName" class="flex-1">
            <el-input v-model="form.realName" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="学号" prop="studentId" class="flex-1">
            <el-input v-model="form.studentId" placeholder="请输入学号" />
          </el-form-item>
        </div>

        <div class="flex gap-3">
          <el-form-item label="学院" prop="college" class="flex-1">
            <el-input v-model="form.college" placeholder="请输入学院" />
          </el-form-item>
          <el-form-item label="专业" prop="major" class="flex-1">
            <el-input v-model="form.major" placeholder="请输入专业" />
          </el-form-item>
        </div>

        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" class="w-full" :loading="loading" @click="handleRegister">注 册</el-button>
        </el-form-item>
      </el-form>

      <div class="text-center text-sm text-gray-500">
        已有账号？<router-link to="/login" class="text-blue-500">返回登录</router-link>
      </div>
    </el-card>
  </div>
</template>
