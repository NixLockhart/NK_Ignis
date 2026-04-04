<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMyProjectsApi, type ProjectInfo } from '@/api/project'
import {
  getApplicationListApi, approveApplicationApi, rejectApplicationApi,
  getApprovedCountApi, batchApproveApplicationApi, batchRejectApplicationApi,
  type ApplicationInfo,
} from '@/api/application'

const loading = ref(false)
const myProjects = ref<ProjectInfo[]>([])
const selectedProjectId = ref<number | null>(null)
const selectedProject = ref<ProjectInfo | null>(null)
const selectedRows = ref<ApplicationInfo[]>([])

const appList = ref<ApplicationInfo[]>([])
const appTotal = ref(0)
const appPage = ref(1)
const appPageSize = ref(10)
const filterStatus = ref('')
const approvedCount = ref(0)

const statusTagType: Record<string, string> = {
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
  cancelled: 'info',
}

// 加载我的项目列表（作为下拉选择）
async function fetchMyProjects() {
  const res = await getMyProjectsApi({ pageSize: 100 })
  myProjects.value = res.data.list
  if (myProjects.value.length > 0 && !selectedProjectId.value) {
    selectedProjectId.value = myProjects.value[0].id
  }
}

// 加载报名列表和名额
async function fetchApplications() {
  if (!selectedProjectId.value) return
  loading.value = true
  try {
    const [appRes, countRes] = await Promise.all([
      getApplicationListApi({
        projectId: selectedProjectId.value,
        status: filterStatus.value || undefined,
        page: appPage.value,
        pageSize: appPageSize.value,
      }),
      getApprovedCountApi(selectedProjectId.value),
    ])
    appList.value = appRes.data.list
    appTotal.value = appRes.data.total
    approvedCount.value = countRes.data.approvedCount
    selectedProject.value = myProjects.value.find((p) => p.id === selectedProjectId.value) || null
  } finally {
    loading.value = false
  }
}

// 切换项目时刷新
watch(selectedProjectId, () => {
  appPage.value = 1
  filterStatus.value = ''
  fetchApplications()
})

async function handleApprove(row: ApplicationInfo) {
  await ElMessageBox.confirm(`确定通过 ${row.userName} 的报名？`, '确认', { type: 'info' })
  await approveApplicationApi(row.id)
  ElMessage.success('已通过')
  fetchApplications()
}

async function handleReject(row: ApplicationInfo) {
  const { value } = await ElMessageBox.prompt('请填写拒绝原因', '拒绝报名', {
    inputType: 'textarea',
    confirmButtonText: '确认拒绝',
    cancelButtonText: '取消',
    inputValidator: (v) => !!v?.trim() || '请输入原因',
  })
  await rejectApplicationApi(row.id, value)
  ElMessage.success('已拒绝')
  fetchApplications()
}

const pendingSelected = computed(() => selectedRows.value.filter(r => r.status === 'pending'))

async function handleBatchApprove() {
  const ids = pendingSelected.value.map(r => r.id)
  if (!ids.length) { ElMessage.warning('请选择待审核的报名'); return }
  await ElMessageBox.confirm(`确定批量通过 ${ids.length} 条报名？`, '批量通过')
  await batchApproveApplicationApi(ids)
  ElMessage.success(`已批量通过 ${ids.length} 条`)
  fetchApplications()
}

async function handleBatchReject() {
  const ids = pendingSelected.value.map(r => r.id)
  if (!ids.length) { ElMessage.warning('请选择待审核的报名'); return }
  const { value } = await ElMessageBox.prompt('请填写批量拒绝原因', '批量拒绝', { inputType: 'textarea', inputValidator: (v) => !!v?.trim() || '请输入原因' })
  await batchRejectApplicationApi(ids, value)
  ElMessage.success(`已批量拒绝 ${ids.length} 条`)
  fetchApplications()
}

function formatTime(time: string | null) {
  if (!time) return '--'
  return time.replace('T', ' ').slice(0, 16)
}

onMounted(fetchMyProjects)
</script>

<template>
  <div>
    <h2 class="text-xl font-bold text-gray-800 mb-4">报名管理</h2>

    <!-- 项目选择 -->
    <div class="flex items-center gap-4 mb-4">
      <el-select v-model="selectedProjectId" placeholder="选择项目" style="width: 300px">
        <el-option v-for="p in myProjects" :key="p.id" :label="p.title" :value="p.id" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="按状态筛选" clearable @change="() => { appPage = 1; fetchApplications() }" style="width: 150px">
        <el-option label="待审核" value="pending" />
        <el-option label="已通过" value="approved" />
        <el-option label="已拒绝" value="rejected" />
      </el-select>
    </div>

    <!-- 名额信息 -->
    <el-alert v-if="selectedProject" :closable="false" class="mb-4" :type="approvedCount >= (selectedProject.maxPeople || 0) ? 'warning' : 'info'">
      <template #title>
        已通过 <strong>{{ approvedCount }}</strong> / 招募 <strong>{{ selectedProject.maxPeople }}</strong> 人
        <el-tag v-if="selectedProject.maxPeople > 0 && approvedCount >= selectedProject.maxPeople" type="danger" size="small" class="ml-2">已满员</el-tag>
      </template>
    </el-alert>

    <!-- 批量操作 -->
    <div v-if="pendingSelected.length > 0" class="mb-3 flex items-center gap-3">
      <span class="text-sm text-gray-500">已选 {{ pendingSelected.length }} 条待审核</span>
      <el-button type="primary" size="small" @click="handleBatchApprove">批量通过</el-button>
      <el-button type="danger" size="small" @click="handleBatchReject">批量拒绝</el-button>
    </div>

    <!-- 报名列表 -->
    <el-table :data="appList" v-loading="loading" stripe @selection-change="(rows: ApplicationInfo[]) => selectedRows = rows">
      <el-table-column type="selection" width="45" />
      <el-table-column prop="userName" label="姓名" width="100" />
      <el-table-column prop="userStudentId" label="学号" width="120" />
      <el-table-column prop="userCollege" label="学院" width="120" />
      <el-table-column prop="applyReason" label="报名说明" min-width="180" />
      <el-table-column label="报名时间" width="170">
        <template #default="{ row }">{{ formatTime(row.applyTime) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTagType[row.status] || 'info'" size="small">{{ row.statusLabel }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-button
              type="primary" text size="small"
              :disabled="selectedProject !== null && selectedProject.maxPeople > 0 && approvedCount >= selectedProject.maxPeople"
              @click="handleApprove(row)"
            >通过</el-button>
            <el-button type="danger" text size="small" @click="handleReject(row)">拒绝</el-button>
          </template>
          <template v-else>
            <span class="text-sm text-gray-400">{{ row.reviewRemark || '--' }}</span>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <div class="flex justify-end mt-4">
      <el-pagination :current-page="appPage" :page-size="appPageSize" :total="appTotal" layout="total, prev, pager, next" @current-change="(p: number) => { appPage = p; fetchApplications() }" />
    </div>

    <el-empty v-if="myProjects.length === 0 && !loading" description="暂无创建的项目" />
  </div>
</template>
