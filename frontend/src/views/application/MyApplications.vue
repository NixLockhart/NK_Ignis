<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMyApplicationsApi, cancelApplicationApi, type ApplicationInfo } from '@/api/application'

const router = useRouter()
const loading = ref(false)
const list = ref<ApplicationInfo[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const filterStatus = ref('')

const statusTagType: Record<string, string> = {
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
  cancelled: 'info',
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getMyApplicationsApi({
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

async function handleCancel(row: ApplicationInfo) {
  await ElMessageBox.confirm('确定取消报名？', '确认', { type: 'warning' })
  await cancelApplicationApi(row.id)
  ElMessage.success('已取消报名')
  fetchList()
}

function formatTime(time: string | null) {
  if (!time) return '--'
  return time.replace('T', ' ').slice(0, 16)
}

function goProject(id: number) {
  router.push(`/project/${id}`)
}

onMounted(fetchList)
</script>

<template>
  <div>
    <h2 class="text-xl font-bold text-gray-800 mb-4">我的报名</h2>

    <div class="mb-4">
      <el-select v-model="filterStatus" placeholder="按状态筛选" clearable @change="() => { page = 1; fetchList() }" style="width: 150px">
        <el-option label="待审核" value="pending" />
        <el-option label="已通过" value="approved" />
        <el-option label="已拒绝" value="rejected" />
        <el-option label="已取消" value="cancelled" />
      </el-select>
    </div>

    <el-table :data="list" v-loading="loading" stripe>
      <el-table-column label="项目名称" min-width="180">
        <template #default="{ row }">
          <el-link type="primary" @click="goProject(row.projectId)">{{ row.projectTitle }}</el-link>
        </template>
      </el-table-column>
      <el-table-column label="报名时间" width="170">
        <template #default="{ row }">{{ formatTime(row.applyTime) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTagType[row.status] || 'info'" size="small">{{ row.statusLabel }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="审核意见" width="180">
        <template #default="{ row }">{{ row.reviewRemark || '--' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending' || row.status === 'approved'" type="danger" text size="small" @click="handleCancel(row)">取消</el-button>
          <el-button v-if="row.status === 'cancelled' || row.status === 'rejected'" type="primary" text size="small" @click="goProject(row.projectId)">重新报名</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="flex justify-end mt-4">
      <el-pagination :current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="(p: number) => { page = p; fetchList() }" />
    </div>
  </div>
</template>
