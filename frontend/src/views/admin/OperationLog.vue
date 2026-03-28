<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getLogListApi, type LogInfo } from '@/api/log'

const loading = ref(false)
const list = ref<LogInfo[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const filterAction = ref('')
const filterDateRange = ref<[string, string] | null>(null)

const actionOptions = [
  { label: '用户登录', value: 'login' },
  { label: '用户注册', value: 'register' },
  { label: '创建项目', value: 'create_project' },
  { label: '提交审核', value: 'submit_project' },
  { label: '审核通过', value: 'approve_project' },
  { label: '审核驳回', value: 'reject_project' },
  { label: '通过报名', value: 'approve_application' },
  { label: '拒绝报名', value: 'reject_application' },
  { label: '签到', value: 'sign_in' },
  { label: '签退', value: 'sign_out' },
  { label: '确认打卡', value: 'confirm_checkin' },
  { label: '评价活动', value: 'create_evaluation' },
  { label: '导出数据', value: 'export_project_stats' },
  { label: '生成证书', value: 'generate_certificate' },
]

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

onMounted(fetchList)
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
      <el-table-column prop="targetType" label="对象类型" width="100" />
      <el-table-column prop="detail" label="操作描述" min-width="250" />
      <el-table-column prop="ipAddress" label="IP" width="130" />
    </el-table>

    <div class="flex justify-end mt-4">
      <el-pagination :current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="(p: number) => { page = p; fetchList() }" />
    </div>
  </div>
</template>
