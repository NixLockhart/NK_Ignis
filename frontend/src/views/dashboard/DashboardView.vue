<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getDashboardApi, type DashboardCard } from '@/api/statistics'
import { getRecommendApi, type RecommendItem } from '@/api/ai'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const cards = ref<DashboardCard[]>([])

const roleMap: Record<string, string> = {
  student: '学生',
  leader: '志愿负责人',
  admin: '管理员',
}

const roleLabel = computed(() => roleMap[userStore.role] || '未知')

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return '上午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const colorClass: Record<string, string> = {
  blue: 'text-blue-500',
  green: 'text-green-500',
  orange: 'text-orange-500',
}

// 项目推荐（学生专属）
const recLoading = ref(false)
const recList = ref<RecommendItem[]>([])

async function fetchDashboard() {
  loading.value = true
  try {
    const res = await getDashboardApi()
    cards.value = res.data.cards
  } finally {
    loading.value = false
  }
}

async function fetchRecommend() {
  recLoading.value = true
  try {
    const res = await getRecommendApi()
    recList.value = res.data
  } catch {
    ElMessage.error('获取推荐失败')
  } finally {
    recLoading.value = false
  }
}

function goProject(id: number) {
  router.push(`/project/${id}`)
}

function formatTime(t: string | null) {
  return t ? t.replace('T', ' ').slice(0, 10) : '--'
}

onMounted(() => {
  fetchDashboard()
  if (userStore.role === 'student') fetchRecommend()
})
</script>

<template>
  <div>
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-gray-800 m-0">
        {{ greeting }}，{{ userStore.userInfo?.realName || userStore.userInfo?.username }}
      </h2>
      <p class="text-gray-500 mt-1">
        当前角色：{{ roleLabel }}
      </p>
    </div>

    <el-row :gutter="16" v-loading="loading">
      <el-col :span="8" v-for="(card, index) in cards" :key="index">
        <el-card shadow="hover">
          <template #header><span class="font-semibold">{{ card.title }}</span></template>
          <div class="text-3xl font-bold text-center py-4" :class="colorClass[card.color] || 'text-blue-500'">
            {{ card.value }} {{ card.unit }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 项目推荐（仅学生） -->
    <div v-if="userStore.role === 'student'" class="mt-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-bold text-gray-800 m-0">
          <el-icon class="mr-1"><MagicStick /></el-icon> 为你推荐
        </h3>
        <el-button type="primary" text :loading="recLoading" @click="fetchRecommend">
          <el-icon><Refresh /></el-icon> 换一批
        </el-button>
      </div>

      <div v-loading="recLoading">
        <el-row :gutter="16" v-if="recList.length > 0">
          <el-col :span="12" v-for="item in recList" :key="item.projectId" class="mb-4">
            <el-card shadow="hover" class="cursor-pointer" @click="goProject(item.projectId)">
              <div class="flex items-start justify-between mb-2">
                <span class="font-semibold text-gray-800">{{ item.title }}</span>
                <el-tag size="small" type="info">{{ item.category || '其他' }}</el-tag>
              </div>
              <div class="text-xs text-gray-400 mb-2 space-y-1">
                <div v-if="item.location"><el-icon><Location /></el-icon> {{ item.location }}</div>
                <div><el-icon><Calendar /></el-icon> {{ formatTime(item.startTime) }} ~ {{ formatTime(item.endTime) }}</div>
                <div><el-icon><User /></el-icon> {{ item.creatorName || '--' }} · 招募{{ item.maxPeople }}人</div>
              </div>
              <div v-if="item.reason" class="text-sm text-blue-600 bg-blue-50 rounded px-2 py-1">
                <el-icon><MagicStick /></el-icon> {{ item.reason }}
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-empty v-if="!recLoading && recList.length === 0" description="暂无推荐项目" />
      </div>
    </div>
  </div>
</template>
