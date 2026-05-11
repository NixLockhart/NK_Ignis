<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getProjectDetailApi, type ProjectInfo } from '@/api/project'
import { applyProjectApi, cancelApplicationApi, getApplicationStatusApi, getApprovedCountApi, type ApplicationInfo } from '@/api/application'
import { signInApi, signOutApi, getCheckinStatusApi, type CheckinInfo } from '@/api/checkin'
import { createEvaluationApi, getEvaluationListApi, type EvaluationInfo } from '@/api/evaluation'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const project = ref<ProjectInfo | null>(null)
const myApplication = ref<ApplicationInfo | null>(null)
const approvedCount = ref(0)
const applyLoading = ref(false)
const myCheckin = ref<CheckinInfo | null>(null)
const checkinLoading = ref(false)
const evaluations = ref<EvaluationInfo[]>([])
const hasEvaluated = ref(false)
const evalDialogVisible = ref(false)
const evalScore = ref(5)
const evalContent = ref('')
const evalLoading = ref(false)

// 已签退可评价
const canEvaluate = computed(() => myCheckin.value?.signOutTime && !hasEvaluated.value)

const statusTagType: Record<string, string> = {
  draft: 'info', pending: 'warning', published: 'success',
  registration_closed: 'warning', in_progress: '', completed: 'info',
}

const isFull = computed(() => {
  if (!project.value || project.value.maxPeople <= 0) return false
  return approvedCount.value >= project.value.maxPeople
})

const isApproved = computed(() => myApplication.value?.status === 'approved')

function formatTime(time: string | null) {
  if (!time) return '--'
  return time.replace('T', ' ').slice(0, 16)
}

async function fetchDetail() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const res = await getProjectDetailApi(id)
    project.value = res.data

    if (userStore.role === 'student') {
      // 获取报名状态和名额
      const [statusRes, countRes] = await Promise.all([
        getApplicationStatusApi(id),
        getApprovedCountApi(id),
      ])
      myApplication.value = statusRes.data
      approvedCount.value = countRes.data.approvedCount

      // 已录取时获取打卡状态
      if (myApplication.value?.status === 'approved') {
        const checkinRes = await getCheckinStatusApi(id)
        myCheckin.value = checkinRes.data
      }
    }

    // 加载评价列表
    const evalRes = await getEvaluationListApi({ projectId: id, pageSize: 50 })
    evaluations.value = evalRes.data.list
    // 检查当前学生是否已评价
    if (userStore.role === 'student') {
      hasEvaluated.value = evaluations.value.some(
        (e) => e.userId === userStore.userInfo?.id && e.evaluatorRole === 'student',
      )
    }
  } finally {
    loading.value = false
  }
}

// 报名
async function handleApply() {
  let reason = ''
  try {
    const { value } = await ElMessageBox.prompt('请填写报名说明（选填）', '报名确认', {
      inputType: 'textarea', confirmButtonText: '确认报名', cancelButtonText: '取消',
    })
    reason = value || ''
  } catch { return }

  applyLoading.value = true
  try {
    await applyProjectApi(Number(route.params.id), reason)
    ElMessage.success('报名成功，等待审核')
    fetchDetail()
  } finally { applyLoading.value = false }
}

async function handleCancelApply() {
  if (!myApplication.value) return
  await ElMessageBox.confirm('确定取消报名？', '确认', { type: 'warning' })
  await cancelApplicationApi(myApplication.value.id)
  ElMessage.success('已取消报名')
  myApplication.value = null
  // 同步刷新项目详情（名额数、报名按钮状态等）
  await fetchDetail()
}

/**
 * 获取当前定位（HTML5 Geolocation）。
 * - 成功：返回 { lat, lng }
 * - 失败 / 不支持 / 拒绝：返回 null（后端会按"未上传位置"处理）
 */
async function _getGeolocation(): Promise<{ lat: number; lng: number } | null> {
  if (typeof navigator === 'undefined' || !navigator.geolocation) {
    return null
  }
  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => resolve(null),
      { timeout: 8000, maximumAge: 30000, enableHighAccuracy: false },
    )
  })
}

// 签到
async function handleSignIn() {
  checkinLoading.value = true
  try {
    const pos = await _getGeolocation()
    await signInApi(Number(route.params.id), pos?.lat, pos?.lng)
    ElMessage.success('签到成功')
    fetchDetail()
  } finally { checkinLoading.value = false }
}

// 签退
async function handleSignOut() {
  await ElMessageBox.confirm('确定签退？签退后将自动计算服务时长。', '确认签退')
  checkinLoading.value = true
  try {
    const pos = await _getGeolocation()
    await signOutApi(Number(route.params.id), pos?.lat, pos?.lng)
    ElMessage.success('签退成功')
    fetchDetail()
  } finally { checkinLoading.value = false }
}

// 评价
async function handleEvaluate() {
  evalLoading.value = true
  try {
    await createEvaluationApi(Number(route.params.id), evalScore.value, evalContent.value)
    ElMessage.success('评价成功')
    evalDialogVisible.value = false
    evalScore.value = 5
    evalContent.value = ''
    fetchDetail()
  } finally {
    evalLoading.value = false
  }
}

onMounted(fetchDetail)
</script>

<template>
  <div v-loading="loading">
    <div class="mb-4">
      <el-button text @click="router.back()">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
    </div>

    <template v-if="project">
      <div class="flex items-center gap-3 mb-6">
        <h2 class="text-2xl font-bold text-gray-800 m-0">{{ project.title }}</h2>
        <el-tag :type="statusTagType[project.status] || 'info'">{{ project.statusLabel }}</el-tag>
      </div>

      <el-descriptions :column="2" border class="mb-6">
        <el-descriptions-item label="活动类型">{{ project.category || '--' }}</el-descriptions-item>
        <el-descriptions-item label="活动地点">{{ project.location || '--' }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ formatTime(project.startTime) }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ formatTime(project.endTime) }}</el-descriptions-item>
        <el-descriptions-item label="报名截止">{{ formatTime(project.registrationDeadline) }}</el-descriptions-item>
        <el-descriptions-item label="招募人数">
          <span>{{ approvedCount }} / {{ project.maxPeople }} 人</span>
          <el-tag v-if="isFull" type="danger" size="small" class="ml-2">已满员</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="联系方式">{{ project.contact || '--' }}</el-descriptions-item>
        <el-descriptions-item label="发起人">{{ project.creatorName || '--' }}</el-descriptions-item>
      </el-descriptions>

      <el-card shadow="never" class="mb-4" v-if="project.content">
        <template #header><span class="font-semibold">活动简介</span></template>
        <div class="whitespace-pre-wrap text-gray-600">{{ project.content }}</div>
      </el-card>

      <el-card shadow="never" class="mb-4" v-if="project.notice">
        <template #header><span class="font-semibold">注意事项</span></template>
        <div class="whitespace-pre-wrap text-gray-600">{{ project.notice }}</div>
      </el-card>

      <el-alert v-if="project.reviewRemark && userStore.role !== 'student'" :title="'审核意见：' + project.reviewRemark" type="info" show-icon :closable="false" class="mb-4" />

      <!-- 学生操作区 -->
      <div v-if="userStore.role === 'student'" class="mt-6">
        <!-- 报名区域 -->
        <template v-if="project.status === 'published'">
          <template v-if="!myApplication">
            <el-button type="primary" size="large" :loading="applyLoading" :disabled="isFull" @click="handleApply">
              {{ isFull ? '名额已满' : '立即报名' }}
            </el-button>
          </template>
          <template v-else-if="myApplication.status === 'pending'">
            <el-tag type="warning" size="large" class="mr-3">报名审核中</el-tag>
            <el-button type="danger" text @click="handleCancelApply">取消报名</el-button>
          </template>
          <template v-else-if="myApplication.status === 'rejected'">
            <el-tag type="danger" size="large">未通过</el-tag>
            <span v-if="myApplication.reviewRemark" class="ml-3 text-sm text-gray-500">原因：{{ myApplication.reviewRemark }}</span>
          </template>
        </template>

        <!-- 签到/签退区域（已录取） -->
        <template v-if="isApproved">
          <el-divider v-if="project.status === 'published'" />
          <div class="flex items-center gap-4">
            <el-tag type="success" size="large">已录取</el-tag>

            <!-- 未打卡 -->
            <template v-if="!myCheckin">
              <el-button type="primary" :loading="checkinLoading" @click="handleSignIn">签到</el-button>
            </template>
            <!-- 已签到未签退 -->
            <template v-else-if="!myCheckin.signOutTime">
              <span class="text-sm text-gray-500">签到时间：{{ formatTime(myCheckin.signInTime) }}</span>
              <el-button type="warning" :loading="checkinLoading" @click="handleSignOut">签退</el-button>
            </template>
            <!-- 已签退 -->
            <template v-else>
              <span class="text-sm text-gray-600">
                服务时长：<strong>{{ myCheckin.durationHours }}</strong> 小时
              </span>
              <el-tag :type="myCheckin.status === 'confirmed' ? 'success' : myCheckin.status === 'rejected' ? 'danger' : 'warning'" size="small">
                {{ myCheckin.statusLabel }}
              </el-tag>
              <el-tag v-if="myCheckin.isAbnormal" type="danger" size="small">异常</el-tag>
            </template>
          </div>
        </template>
      </div>

      <!-- 评价区域 -->
      <el-divider v-if="evaluations.length > 0 || canEvaluate" />

      <!-- 评价按钮（学生已签退且未评价） -->
      <div v-if="canEvaluate && userStore.role === 'student'" class="mb-4">
        <el-button type="primary" @click="evalDialogVisible = true">
          <el-icon><Star /></el-icon> 评价本次活动
        </el-button>
      </div>
      <div v-if="hasEvaluated && userStore.role === 'student'" class="mb-4">
        <el-tag type="success">已评价</el-tag>
      </div>

      <!-- 评价列表 -->
      <el-card v-if="evaluations.length > 0" shadow="never">
        <template #header><span class="font-semibold">活动评价（{{ evaluations.length }}条）</span></template>
        <div v-for="ev in evaluations" :key="ev.id" class="mb-4 pb-4 border-b border-gray-100 last:border-b-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="font-medium text-gray-700">{{ ev.userName }}</span>
            <el-tag size="small" :type="ev.evaluatorRole === 'leader' ? 'warning' : ''">
              {{ ev.evaluatorRole === 'leader' ? '负责人评语' : '学生评价' }}
            </el-tag>
            <el-rate :model-value="ev.score" disabled size="small" />
            <span class="text-xs text-gray-400 ml-auto">{{ ev.createdAt?.replace('T', ' ').slice(0, 16) }}</span>
          </div>
          <div v-if="ev.content" class="text-sm text-gray-600">{{ ev.content }}</div>
        </div>
      </el-card>

      <!-- 评价弹窗 -->
      <el-dialog v-model="evalDialogVisible" title="评价活动" width="400px" destroy-on-close>
        <el-form label-position="top">
          <el-form-item label="评分">
            <el-rate v-model="evalScore" :max="5" show-text :texts="['很差', '较差', '一般', '较好', '很好']" />
          </el-form-item>
          <el-form-item label="评价内容（选填）">
            <el-input v-model="evalContent" type="textarea" :rows="3" placeholder="请输入您的评价" maxlength="500" show-word-limit />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="evalDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="evalLoading" @click="handleEvaluate">提交评价</el-button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>
