<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMyProjectsApi, type ProjectInfo } from '@/api/project'
import { getCheckinListApi, confirmCheckinApi, rejectCheckinApi, type CheckinInfo } from '@/api/checkin'

const loading = ref(false)
const myProjects = ref<ProjectInfo[]>([])
const selectedProjectId = ref<number | null>(null)

const list = ref<CheckinInfo[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const filterStatus = ref('')

const statusTagType: Record<string, string> = {
  pending: 'warning', confirmed: 'success', rejected: 'danger',
}

async function fetchMyProjects() {
  const res = await getMyProjectsApi({ pageSize: 100 })
  myProjects.value = res.data.list
  if (myProjects.value.length > 0 && !selectedProjectId.value) {
    selectedProjectId.value = myProjects.value[0].id
  }
}

async function fetchCheckins() {
  if (!selectedProjectId.value) return
  loading.value = true
  try {
    const res = await getCheckinListApi({
      projectId: selectedProjectId.value,
      status: filterStatus.value || undefined,
      page: page.value,
      pageSize: pageSize.value,
    })
    list.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

watch(selectedProjectId, () => {
  page.value = 1
  filterStatus.value = ''
  fetchCheckins()
})

async function handleConfirm(row: CheckinInfo) {
  await ElMessageBox.confirm(`确定确认 ${row.userName} 的打卡记录？（${row.durationHours}h）`, '确认')
  await confirmCheckinApi(row.id)
  ElMessage.success('已确认')
  fetchCheckins()
}

async function handleReject(row: CheckinInfo) {
  const { value } = await ElMessageBox.prompt('请填写驳回原因', '驳回打卡', {
    inputType: 'textarea',
    confirmButtonText: '确认驳回',
    cancelButtonText: '取消',
  })
  await rejectCheckinApi(row.id, value || '')
  ElMessage.success('已驳回')
  fetchCheckins()
}

function formatTime(time: string | null) {
  if (!time) return '--'
  return time.replace('T', ' ').slice(0, 16)
}

onMounted(fetchMyProjects)
</script>

<template>
  <div>
    <h2 class="text-xl font-bold text-gray-800 mb-4">打卡管理</h2>

    <div class="flex items-center gap-4 mb-4">
      <el-select v-model="selectedProjectId" placeholder="选择项目" style="width: 300px">
        <el-option v-for="p in myProjects" :key="p.id" :label="p.title" :value="p.id" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="按状态筛选" clearable @change="() => { page = 1; fetchCheckins() }" style="width: 150px">
        <el-option label="待确认" value="pending" />
        <el-option label="已确认" value="confirmed" />
        <el-option label="已驳回" value="rejected" />
      </el-select>
    </div>

    <el-table :data="list" v-loading="loading" stripe :row-class-name="({ row }: { row: CheckinInfo }) => row.isAbnormal ? 'bg-red-50' : ''">
      <el-table-column prop="userName" label="姓名" width="100" />
      <el-table-column prop="userStudentId" label="学号" width="120" />
      <el-table-column label="签到时间" width="170">
        <template #default="{ row }">{{ formatTime(row.signInTime) }}</template>
      </el-table-column>
      <el-table-column label="签退时间" width="170">
        <template #default="{ row }">{{ formatTime(row.signOutTime) }}</template>
      </el-table-column>
      <el-table-column label="时长(h)" width="90" align="center">
        <template #default="{ row }">{{ row.durationHours ?? '--' }}</template>
      </el-table-column>
      <el-table-column label="异常" width="70" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.isAbnormal" type="danger" size="small">异常</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTagType[row.status] || 'info'" size="small">{{ row.statusLabel }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'pending' && row.signOutTime">
            <el-button type="primary" text size="small" @click="handleConfirm(row)">确认</el-button>
            <el-button type="danger" text size="small" @click="handleReject(row)">驳回</el-button>
          </template>
          <template v-else-if="row.status === 'pending' && !row.signOutTime">
            <el-text type="warning" size="small">未签退</el-text>
          </template>
          <template v-else>
            <span class="text-sm text-gray-400">{{ row.remark || (row.status === 'confirmed' ? '已确认' : '--') }}</span>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <div class="flex justify-end mt-4">
      <el-pagination :current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="(p: number) => { page = p; fetchCheckins() }" />
    </div>

    <el-empty v-if="myProjects.length === 0 && !loading" description="暂无创建的项目" />
  </div>
</template>
