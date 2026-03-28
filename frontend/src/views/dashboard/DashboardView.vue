<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { getDashboardApi, type DashboardCard } from '@/api/statistics'

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

// 颜色映射
const colorClass: Record<string, string> = {
  blue: 'text-blue-500',
  green: 'text-green-500',
  orange: 'text-orange-500',
}

async function fetchDashboard() {
  loading.value = true
  try {
    const res = await getDashboardApi()
    cards.value = res.data.cards
  } finally {
    loading.value = false
  }
}

onMounted(fetchDashboard)
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
  </div>
</template>
