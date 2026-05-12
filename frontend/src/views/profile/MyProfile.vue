<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getTotalHoursApi, getHoursDetailApi, type HoursDetail } from '@/api/checkin'
import { getMyEvaluationsApi, type EvaluationInfo } from '@/api/evaluation'
import { getMyCertificateListApi, type CertificateItem } from '@/api/certificate'
import { updateProfileApi, changePasswordApi } from '@/api/auth'
import { getCollegeListApi, type CollegeItem } from '@/api/college'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const totalHours = ref(0)
const hoursDetail = ref<HoursDetail[]>([])
const evaluations = ref<EvaluationInfo[]>([])
const certificates = ref<CertificateItem[]>([])

async function fetchData() {
  loading.value = true
  try {
    const [hoursRes, detailRes, evalRes, certRes] = await Promise.all([
      getTotalHoursApi(),
      getHoursDetailApi(),
      getMyEvaluationsApi({ pageSize: 50 }),
      getMyCertificateListApi(),
    ])
    totalHours.value = hoursRes.data.totalHours
    hoursDetail.value = detailRes.data
    evaluations.value = evalRes.data.list
    certificates.value = certRes.data
  } finally {
    loading.value = false
  }
}

function formatTime(time: string | null) {
  if (!time) return '--'
  return time.replace('T', ' ').slice(0, 16)
}

function goCertificate(projectId: number) {
  router.push(`/certificate/${projectId}`)
}

// ========== 编辑个人信息 ==========

const editDialogVisible = ref(false)
const editFormRef = ref<FormInstance>()
const collegeList = ref<CollegeItem[]>([])
const editForm = reactive({
  realName: '',
  college: '',
  major: '',
  phone: '',
  email: '',
})
const editLoading = ref(false)

const editRules: FormRules = {
  realName: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, max: 20, message: '姓名长度需在 2 到 20 个字符之间', trigger: 'blur' },
  ],
  college: [{ required: true, message: '请选择学院', trigger: 'change' }],
  major: [{ required: true, message: '请输入专业', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
  email: [
    {
      validator: (_rule, value, callback) => {
        if (!value) { callback(); return }
        if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) { callback() } else { callback(new Error('邮箱格式不正确')) }
      },
      trigger: 'blur',
    },
  ],
}

function openEditDialog() {
  const info = userStore.userInfo
  if (info) {
    editForm.realName = info.realName
    editForm.college = info.college
    editForm.major = info.major
    editForm.phone = info.phone
    editForm.email = info.email || ''
  }
  editDialogVisible.value = true
}

async function handleSaveProfile() {
  const valid = await editFormRef.value?.validate().catch(() => false)
  if (!valid) return
  editLoading.value = true
  try {
    await updateProfileApi(editForm)
    await userStore.fetchProfile()
    editDialogVisible.value = false
    ElMessage.success('信息更新成功')
  } catch {
    // 错误已在拦截器处理
  } finally {
    editLoading.value = false
  }
}

// ========== 修改密码 ==========

const passwordDialogVisible = ref(false)
const passwordFormRef = ref<FormInstance>()
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})
const passwordLoading = ref(false)

const passwordRules: FormRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度需在 6 到 20 个字符之间', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

function openPasswordDialog() {
  passwordForm.oldPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  passwordDialogVisible.value = true
}

async function handleChangePassword() {
  const valid = await passwordFormRef.value?.validate().catch(() => false)
  if (!valid) return
  passwordLoading.value = true
  try {
    await changePasswordApi(passwordForm.oldPassword, passwordForm.newPassword)
    passwordDialogVisible.value = false
    ElMessage.success('密码修改成功，请重新登录')
    // 强制重新登录
    userStore.logout()
    router.push('/login')
  } catch {
    // 错误已在拦截器处理
  } finally {
    passwordLoading.value = false
  }
}

onMounted(() => {
  fetchData()
  getCollegeListApi().then(res => { collegeList.value = res.data }).catch(() => {})
})
</script>

<template>
  <div v-loading="loading">
    <h2 class="text-xl font-bold text-gray-800 mb-4">个人服务档案</h2>

    <!-- 个人信息 -->
    <el-card shadow="never" class="mb-4">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="font-semibold">基本信息</span>
          <div class="flex gap-2">
            <el-button type="primary" text size="small" @click="openEditDialog">编辑信息</el-button>
            <el-button type="warning" text size="small" @click="openPasswordDialog">修改密码</el-button>
          </div>
        </div>
      </template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="姓名">{{ userStore.userInfo?.realName }}</el-descriptions-item>
        <el-descriptions-item label="学号">{{ userStore.userInfo?.studentId }}</el-descriptions-item>
        <el-descriptions-item label="学院">{{ userStore.userInfo?.college }}</el-descriptions-item>
        <el-descriptions-item label="专业">{{ userStore.userInfo?.major }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ userStore.userInfo?.phone }}</el-descriptions-item>
        <el-descriptions-item label="角色">学生</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="mb-4">
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-sm text-gray-500">已参加项目</div>
            <div class="text-3xl font-bold text-blue-500 mt-1">{{ hoursDetail.length }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-sm text-gray-500">累计服务时长</div>
            <div class="text-3xl font-bold text-green-500 mt-1">{{ totalHours }} h</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-sm text-gray-500">可获得证书</div>
            <div class="text-3xl font-bold text-orange-500 mt-1">{{ certificates.length }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 时长明细 -->
    <el-card shadow="never" class="mb-4">
      <template #header><span class="font-semibold">服务时长明细</span></template>
      <el-table :data="hoursDetail" stripe size="small">
        <el-table-column prop="projectTitle" label="项目名称" min-width="180" />
        <el-table-column label="签到时间" width="170">
          <template #default="{ row }">{{ formatTime(row.signInTime) }}</template>
        </el-table-column>
        <el-table-column label="签退时间" width="170">
          <template #default="{ row }">{{ formatTime(row.signOutTime) }}</template>
        </el-table-column>
        <el-table-column label="时长(h)" width="90" align="center">
          <template #default="{ row }">{{ row.durationHours }}</template>
        </el-table-column>
      </el-table>
      <el-empty v-if="hoursDetail.length === 0" description="暂无服务记录" />
    </el-card>

    <!-- 证书列表 -->
    <el-card shadow="never" class="mb-4">
      <template #header><span class="font-semibold">可获得的证书</span></template>
      <el-table :data="certificates" stripe size="small">
        <el-table-column prop="projectTitle" label="项目名称" min-width="200" />
        <el-table-column label="服务时长" width="100" align="center">
          <template #default="{ row }">{{ row.durationHours }} h</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" text size="small" @click="goCertificate(row.projectId)">查看证书</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="certificates.length === 0" description="暂无可获得的证书" />
    </el-card>

    <!-- 评价记录 -->
    <el-card shadow="never">
      <template #header><span class="font-semibold">我的评价记录</span></template>
      <div v-for="ev in evaluations" :key="ev.id" class="mb-3 pb-3 border-b border-gray-100 last:border-b-0">
        <div class="flex items-center gap-2 mb-1">
          <span class="font-medium">{{ ev.projectTitle }}</span>
          <el-rate :model-value="ev.score" disabled size="small" />
          <span class="text-xs text-gray-400 ml-auto">{{ ev.createdAt?.replace('T', ' ').slice(0, 16) }}</span>
        </div>
        <div v-if="ev.content" class="text-sm text-gray-600">{{ ev.content }}</div>
      </div>
      <el-empty v-if="evaluations.length === 0" description="暂无评价记录" />
    </el-card>

    <!-- 编辑个人信息弹窗 -->
    <el-dialog v-model="editDialogVisible" title="编辑个人信息" width="450px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="80px">
        <el-form-item label="姓名" prop="realName">
          <el-input v-model="editForm.realName" />
        </el-form-item>
        <el-form-item label="学院" prop="college">
          <el-select v-model="editForm.college" placeholder="选择学院" filterable style="width: 100%">
            <el-option v-for="c in collegeList" :key="c.id" :label="c.name" :value="c.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="专业" prop="major">
          <el-input v-model="editForm.major" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="editForm.phone" maxlength="11" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" placeholder="可选" maxlength="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editLoading" @click="handleSaveProfile">保存</el-button>
      </template>
    </el-dialog>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="passwordDialogVisible" title="修改密码" width="420px">
      <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="90px">
        <el-form-item label="原密码" prop="oldPassword">
          <el-input v-model="passwordForm.oldPassword" type="password" show-password placeholder="请输入原密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password placeholder="6-20 位字符" />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password placeholder="再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>
