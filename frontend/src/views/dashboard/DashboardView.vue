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

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return '上午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const cardIcons: Record<string, { icon: string; bg: string }> = {
  blue: { icon: 'Tickets', bg: 'bg-blue-50 text-blue-500' },
  green: { icon: 'User', bg: 'bg-green-50 text-green-500' },
  orange: { icon: 'Clock', bg: 'bg-orange-50 text-orange-500' },
}

const recLoading = ref(false)
const recList = ref<RecommendItem[]>([])

async function fetchDashboard() {
  loading.value = true
  try { const res = await getDashboardApi(); cards.value = res.data.cards } finally { loading.value = false }
}

// 按用户隔离缓存键，避免同标签页登出 A 登入 B 时仍看到 A 的推荐
const cacheKey = computed(() => `rec_cache_${userStore.userInfo?.id ?? 'anon'}`)

async function fetchRecommend(forceRefresh = false) {
  if (!forceRefresh) {
    try {
      const cached = sessionStorage.getItem(cacheKey.value)
      if (cached) { recList.value = JSON.parse(cached); return }
    } catch { /* ignore */ }
  }
  recLoading.value = true
  try {
    const res = await getRecommendApi()
    recList.value = res.data
    sessionStorage.setItem(cacheKey.value, JSON.stringify(res.data))
  } catch { ElMessage.error('获取推荐失败') } finally { recLoading.value = false }
}

function goProject(id: number) { router.push(`/project/${id}`) }
function formatTime(t: string | null) { return t ? t.replace('T', ' ').slice(0, 10) : '--' }

onMounted(() => {
  fetchDashboard()
  if (userStore.role === 'student') fetchRecommend()
})
</script>

<template>
  <div>
    <!-- 欢迎横幅 -->
    <div class="relative rounded-2xl overflow-hidden mb-6 p-6 md:p-8 bg-gradient-to-r from-[#4F6EF7] via-[#6C8CFA] to-[#36CFC9] text-white">
      <div class="absolute -top-10 -right-10 w-40 h-40 bg-white/10 rounded-full"></div>
      <div class="absolute -bottom-8 right-20 w-28 h-28 bg-white/5 rounded-full"></div>
      <div class="relative z-10">
        <h2 class="text-xl md:text-2xl font-bold m-0">
          {{ greeting }}，{{ userStore.userInfo?.realName || userStore.userInfo?.username }} 👋
        </h2>
        <p class="text-sm opacity-80 mt-2">欢迎使用志愿服务管理系统，祝您今天工作顺利</p>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" v-loading="loading" class="mb-6">
      <el-col :xs="24" :sm="12" :lg="8" v-for="(card, index) in cards" :key="index" class="mb-4 lg:mb-0">
        <div class="bg-white rounded-xl p-5 card-hover border border-gray-100">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0" :class="cardIcons[card.color]?.bg || 'bg-blue-50 text-blue-500'">
              <el-icon size="24"><component :is="cardIcons[card.color]?.icon || 'Tickets'" /></el-icon>
            </div>
            <div>
              <div class="text-xs text-gray-400">{{ card.title }}</div>
              <div class="text-2xl font-bold text-gray-800 mt-0.5" style="font-variant-numeric: tabular-nums;">
                {{ card.value }} <span class="text-sm font-normal text-gray-400">{{ card.unit }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 项目推荐（仅学生） -->
    <div v-if="userStore.role === 'student'">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-base font-bold text-gray-800 m-0 flex items-center gap-2">
          <span class="w-1 h-5 bg-[#4F6EF7] rounded-full inline-block"></span>
          为你推荐
        </h3>
        <el-button type="primary" text :loading="recLoading" @click="fetchRecommend(true)">
          <el-icon><Refresh /></el-icon> 换一批
        </el-button>
      </div>

      <div v-loading="recLoading">
        <el-row :gutter="16" v-if="recList.length > 0">
          <el-col :xs="24" :sm="12" v-for="item in recList" :key="item.projectId" class="mb-4">
            <div class="bg-white rounded-xl p-4 card-hover border border-gray-100 cursor-pointer" @click="goProject(item.projectId)">
              <div class="flex items-start justify-between mb-2">
                <span class="font-semibold text-gray-800 text-sm">{{ item.title }}</span>
                <el-tag size="small" round type="info">{{ item.category || '其他' }}</el-tag>
              </div>
              <div class="text-xs text-gray-400 mb-2 space-y-1">
                <div v-if="item.location"><el-icon size="12"><Location /></el-icon> {{ item.location }}</div>
                <div><el-icon size="12"><Calendar /></el-icon> {{ formatTime(item.startTime) }} ~ {{ formatTime(item.endTime) }}</div>
                <div><el-icon size="12"><User /></el-icon> {{ item.creatorName || '--' }} · 招募{{ item.maxPeople }}人</div>
              </div>
              <div v-if="item.reason" class="text-xs text-[#4F6EF7] bg-[#EEF1FE] rounded-lg px-3 py-1.5 mt-2">
                <el-icon size="12"><MagicStick /></el-icon> {{ item.reason }}
              </div>
            </div>
          </el-col>
        </el-row>
        <el-empty v-if="!recLoading && recList.length === 0" description="暂无推荐项目" :image-size="80" />
      </div>
    </div>
  </div>
</template>
