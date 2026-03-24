<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getMyCheckinsApi, getTotalHoursApi, type CheckinInfo } from '@/api/checkin'

const router = useRouter()
const loading = ref(false)
const list = ref<CheckinInfo[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const totalHours = ref(0)

const statusTagType: Record<string, string> = {
  pending: 'warning', confirmed: 'success', rejected: 'danger',
}

async function fetchData() {
  loading.value = true
  try {
    const [listRes, hoursRes] = await Promise.all([
      getMyCheckinsApi({ page: page.value, pageSize: pageSize.value }),
      getTotalHoursApi(),
    ])
    list.value = listRes.data.list
    total.value = listRes.data.total
    totalHours.value = hoursRes.data.totalHours
  } finally {
    loading.value = false
  }
}

function formatTime(time: string | null) {
  if (!time) return '--'
  return time.replace('T', ' ').slice(0, 16)
}

function goProject(id: number) {
  router.push(`/project/${id}`)
}

onMounted(fetchData)
</script>

<template>
  <div>
    <h2 class="text-xl font-bold text-gray-800 mb-4">我的打卡记录</h2>

    <el-card shadow="never" class="mb-4">
      <div class="text-center">
        <div class="text-sm text-gray-500">累计已确认服务时长</div>
        <div class="text-3xl font-bold text-green-500 mt-1">{{ totalHours }} 小时</div>
      </div>
    </el-card>

    <el-table :data="list" v-loading="loading" stripe>
      <el-table-column label="项目名称" min-width="180">
        <template #default="{ row }">
          <el-link type="primary" @click="goProject(row.projectId)">{{ row.projectTitle }}</el-link>
        </template>
      </el-table-column>
      <el-table-column label="签到时间" width="170">
        <template #default="{ row }">{{ formatTime(row.signInTime) }}</template>
      </el-table-column>
      <el-table-column label="签退时间" width="170">
        <template #default="{ row }">{{ formatTime(row.signOutTime) }}</template>
      </el-table-column>
      <el-table-column label="时长(h)" width="90" align="center">
        <template #default="{ row }">{{ row.durationHours ?? '--' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTagType[row.status] || 'info'" size="small">{{ row.statusLabel }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="异常" width="70" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.isAbnormal" type="danger" size="small">异常</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="备注" width="150">
        <template #default="{ row }">{{ row.remark || '--' }}</template>
      </el-table-column>
    </el-table>

    <div class="flex justify-end mt-4">
      <el-pagination :current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="(p: number) => { page = p; fetchData() }" />
    </div>
  </div>
</template>
