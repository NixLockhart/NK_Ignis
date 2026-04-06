<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { registerApi, type RegisterParams } from '@/api/auth'
import { getCollegeListApi, type CollegeItem } from '@/api/college'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Postcard, Tickets, Phone } from '@element-plus/icons-vue'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const collegeList = ref<CollegeItem[]>([])

const form = reactive<RegisterParams & { confirmPassword: string }>({
  username: '', password: '', confirmPassword: '',
  realName: '', studentId: '', college: '', major: '', phone: '',
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
    { validator: (_rule, value, callback) => { value !== form.password ? callback(new Error('两次输入的密码不一致')) : callback() }, trigger: 'blur' },
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
  } catch { /* 错误已在拦截器中处理 */ } finally { loading.value = false }
}

onMounted(async () => {
  try { const res = await getCollegeListApi(); collegeList.value = res.data } catch { /* ignore */ }
})
</script>

<template>
  <div class="min-h-screen flex">
    <!-- 左侧插画区 -->
    <div class="hidden lg:flex lg:w-[58%] bg-gradient-to-br from-[#36CFC9] via-[#4F6EF7] to-[#6C8CFA] items-center justify-center relative overflow-hidden">
      <div class="absolute -top-20 -left-20 w-80 h-80 bg-white/10 rounded-full"></div>
      <div class="absolute -bottom-32 -right-32 w-96 h-96 bg-white/5 rounded-full"></div>
      <div class="relative z-10 text-center text-white px-12">
        <div class="text-5xl mb-6">✨</div>
        <h1 class="text-3xl font-bold mb-4">加入志愿者大家庭</h1>
        <p class="text-sm opacity-70 max-w-sm mx-auto leading-relaxed">
          注册成为志愿者，探索丰富的志愿项目，用行动传递温暖，让爱心发光
        </p>
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="flex-1 flex items-center justify-center bg-[#F7F8FC] px-6 py-8">
      <div class="w-full max-w-md">
        <div class="text-center mb-6">
          <div class="lg:hidden text-4xl mb-3">✨</div>
          <h2 class="text-2xl font-bold text-gray-800">注册新账号</h2>
          <p class="text-sm text-gray-400 mt-2">填写以下信息完成注册</p>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" :prefix-icon="User" />
          </el-form-item>

          <div class="flex gap-3">
            <el-form-item label="密码" prop="password" class="flex-1">
              <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password :prefix-icon="Lock" />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword" class="flex-1">
              <el-input v-model="form.confirmPassword" type="password" placeholder="请确认密码" show-password :prefix-icon="Lock" />
            </el-form-item>
          </div>

          <div class="flex gap-3">
            <el-form-item label="真实姓名" prop="realName" class="flex-1">
              <el-input v-model="form.realName" placeholder="请输入姓名" :prefix-icon="Postcard" />
            </el-form-item>
            <el-form-item label="学号" prop="studentId" class="flex-1">
              <el-input v-model="form.studentId" placeholder="请输入学号" :prefix-icon="Tickets" />
            </el-form-item>
          </div>

          <div class="flex gap-3">
            <el-form-item label="学院" prop="college" class="flex-1">
              <el-select v-model="form.college" placeholder="选择学院" filterable>
                <el-option v-for="c in collegeList" :key="c.id" :label="c.name" :value="c.name" />
              </el-select>
            </el-form-item>
            <el-form-item label="专业" prop="major" class="flex-1">
              <el-input v-model="form.major" placeholder="请输入专业" />
            </el-form-item>
          </div>

          <el-form-item label="手机号" prop="phone">
            <el-input v-model="form.phone" placeholder="请输入手机号" :prefix-icon="Phone" />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" class="w-full !h-11 !text-base !rounded-lg" :loading="loading" @click="handleRegister">注 册</el-button>
          </el-form-item>
        </el-form>

        <div class="text-center text-sm text-gray-400">
          已有账号？<router-link to="/login" class="text-[#4F6EF7] font-medium hover:underline">返回登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>
