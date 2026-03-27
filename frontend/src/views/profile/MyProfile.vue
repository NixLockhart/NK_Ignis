<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getTotalHoursApi, getHoursDetailApi, type HoursDetail } from '@/api/checkin'
import { getMyEvaluationsApi, type EvaluationInfo } from '@/api/evaluation'
import { getMyCertificateListApi, type CertificateItem } from '@/api/certificate'
import { updateProfileApi } from '@/api/auth'
import { ElMessage } from 'element-plus'

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

// 编辑个人信息
const editDialogVisible = ref(false)
const editForm = reactive({
  realName: '',
  college: '',
  major: '',
  phone: '',
})
const editLoading = ref(false)

function openEditDialog() {
  const info = userStore.userInfo
  if (info) {
    editForm.realName = info.realName
    editForm.college = info.college
    editForm.major = info.major
    editForm.phone = info.phone
  }
  editDialogVisible.value = true
}

async function handleSaveProfile() {
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

onMounted(fetchData)
</script>

<template>
  <div v-loading="loading">
    <h2 class="text-xl font-bold text-gray-800 mb-4">个人服务档案</h2>

    <!-- 个人信息 -->
    <el-card shadow="never" class="mb-4">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="font-semibold">基本信息</span>
          <el-button type="primary" text size="small" @click="openEditDialog">编辑信息</el-button>
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
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="姓名">
          <el-input v-model="editForm.realName" />
        </el-form-item>
        <el-form-item label="学院">
          <el-input v-model="editForm.college" />
        </el-form-item>
        <el-form-item label="专业">
          <el-input v-model="editForm.major" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="editForm.phone" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editLoading" @click="handleSaveProfile">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
