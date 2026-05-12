<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getLogListApi, getActionTypesApi, type LogInfo, type ActionTypeOption } from '@/api/log'

const loading = ref(false)
const list = ref<LogInfo[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const filterAction = ref('')
const filterDateRange = ref<[string, string] | null>(null)

// 操作类型选项从后端动态加载，与 OperationLog.ACTION_LABELS 同源
const actionOptions = ref<ActionTypeOption[]>([])

// 操作对象类型中文映射（前端展示用）
const TARGET_TYPE_LABELS: Record<string, string> = {
  user: '用户',
  project: '项目',
  application: '报名',
  checkin: '打卡',
  evaluation: '评价',
  certificate: '证书',
  college: '学院',
}

async function fetchActionTypes() {
  try {
    const res = await getActionTypesApi()
    actionOptions.value = res.data
  } catch {
    /* 拦截器已提示 */
  }
}

async function fetchList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: page.value,
      pageSize: pageSize.value,
    }
    if (filterAction.value) params.action = filterAction.value
    if (filterDateRange.value) {
      params.startDate = filterDateRange.value[0]
      params.endDate = filterDateRange.value[1]
    }

    const res = await getLogListApi(params as Parameters<typeof getLogListApi>[0])
    list.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function handleFilter() {
  page.value = 1
  fetchList()
}

function formatTime(time: string | null) {
  if (!time) return '--'
  return time.replace('T', ' ').slice(0, 19)
}

onMounted(async () => {
  await fetchActionTypes()
  await fetchList()
})
</script>

<template>
  <div>
    <h2 class="text-xl font-bold text-gray-800 mb-4">操作日志</h2>

    <!-- 筛选栏 -->
    <div class="flex gap-3 mb-4 flex-wrap">
      <el-select v-model="filterAction" placeholder="操作类型" clearable @change="handleFilter" style="width: 160px">
        <el-option v-for="opt in actionOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
      <el-date-picker
        v-model="filterDateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        @change="handleFilter"
      />
    </div>

    <!-- 日志表格 -->
    <el-table :data="list" v-loading="loading" stripe size="small">
      <el-table-column label="时间" width="170">
        <template #default="{ row }">{{ formatTime(row.createdAt) }}</template>
      </el-table-column>
      <el-table-column prop="userName" label="操作人" width="100" />
      <el-table-column prop="actionLabel" label="操作类型" width="120" />
      <el-table-column label="对象类型" width="100">
        <template #default="{ row }">
          {{ row.targetType ? (TARGET_TYPE_LABELS[row.targetType] || row.targetType) : '--' }}
        </template>
      </el-table-column>
      <el-table-column prop="detail" label="操作描述" min-width="250" />
      <el-table-column prop="ipAddress" label="IP" width="130" />
    </el-table>

    <div class="flex justify-end mt-4">
      <el-pagination :current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="(p: number) => { page = p; fetchList() }" />
    </div>
  </div>
</template>
