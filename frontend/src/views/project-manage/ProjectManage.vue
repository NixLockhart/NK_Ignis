<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getMyProjectsApi, deleteProjectApi, submitProjectApi,
  type ProjectInfo, type ProjectFormData,
} from '@/api/project'
import { downloadBatchCertificateZipApi } from '@/api/certificate'
import ProjectForm from './ProjectForm.vue'

const router = useRouter()
const loading = ref(false)
const projectList = ref<ProjectInfo[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const filterStatus = ref('')

// 表单弹窗
const formVisible = ref(false)
const editData = ref<ProjectFormData | null>(null)

// 批量证书弹窗
const batchDialogVisible = ref(false)
const batchProject = ref<ProjectInfo | null>(null)
const batchLoading = ref(false)

const statusTagType: Record<string, string> = {
  draft: 'info',
  pending: 'warning',
  published: 'success',
  registration_closed: 'warning',
  in_progress: '',
  completed: 'info',
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getMyProjectsApi({
      status: filterStatus.value || undefined,
      page: page.value,
      pageSize: pageSize.value,
    })
    projectList.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function handleCreate() {
  editData.value = null
  formVisible.value = true
}

function handleEdit(row: ProjectInfo) {
  editData.value = {
    id: row.id,
    title: row.title,
    content: row.content,
    location: row.location,
    category: row.category,
    startTime: row.startTime || '',
    endTime: row.endTime || '',
    registrationDeadline: row.registrationDeadline || '',
    maxPeople: row.maxPeople,
    contact: row.contact,
    notice: row.notice,
  }
  formVisible.value = true
}

async function handleDelete(row: ProjectInfo) {
  await ElMessageBox.confirm('确定删除该项目？', '确认删除', { type: 'warning' })
  await deleteProjectApi(row.id)
  ElMessage.success('删除成功')
  fetchList()
}

async function handleSubmit(row: ProjectInfo) {
  await ElMessageBox.confirm('确定提交审核？提交后将无法编辑。', '确认提交', { type: 'info' })
  await submitProjectApi(row.id)
  ElMessage.success('已提交审核')
  fetchList()
}

function goDetail(id: number) {
  router.push(`/project/${id}`)
}

function handlePageChange(p: number) {
  page.value = p
  fetchList()
}

function handleFilter() {
  page.value = 1
  fetchList()
}

async function openBatchCertificate(row: ProjectInfo) {
  batchProject.value = row
  batchDialogVisible.value = true
}

async function handleBatchDownload() {
  if (!batchProject.value) return
  batchLoading.value = true
  try {
    await downloadBatchCertificateZipApi(batchProject.value.id)
    ElMessage.success('证书 ZIP 已开始下载')
    batchDialogVisible.value = false
  } catch {
    /* */
  } finally {
    batchLoading.value = false
  }
}

onMounted(fetchList)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-xl font-bold text-gray-800 m-0">项目管理</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新建项目
      </el-button>
    </div>

    <!-- 筛选 -->
    <div class="mb-4">
      <el-select v-model="filterStatus" placeholder="按状态筛选" clearable @change="handleFilter" style="width: 150px">
        <el-option label="草稿" value="draft" />
        <el-option label="待审核" value="pending" />
        <el-option label="已发布" value="published" />
        <el-option label="进行中" value="in_progress" />
        <el-option label="已结束" value="completed" />
      </el-select>
    </div>

    <!-- 表格 -->
    <el-table :data="projectList" v-loading="loading" stripe>
      <el-table-column prop="title" label="项目名称" min-width="180">
        <template #default="{ row }">
          <el-link type="primary" @click="goDetail(row.id)">{{ row.title }}</el-link>
        </template>
      </el-table-column>
      <el-table-column prop="category" label="类型" width="100" />
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTagType[row.status] || 'info'" size="small">{{ row.statusLabel }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="招募人数" width="90" align="center">
        <template #default="{ row }">{{ row.maxPeople }}</template>
      </el-table-column>
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">{{ row.createdAt?.replace('T', ' ').slice(0, 16) || '--' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'draft'">
            <el-button type="primary" text size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="warning" text size="small" @click="handleSubmit(row)">提交审核</el-button>
            <el-button type="danger" text size="small" @click="handleDelete(row)">删除</el-button>
          </template>
          <template v-else-if="row.status === 'pending'">
            <el-text type="warning" size="small">审核中</el-text>
          </template>
          <template v-else>
            <el-button type="primary" text size="small" @click="goDetail(row.id)">查看</el-button>
            <el-button
              v-if="['in_progress', 'completed'].includes(row.status)"
              type="success" text size="small"
              @click="openBatchCertificate(row)"
            >批量证书</el-button>
          </template>
          <el-text v-if="row.reviewRemark" type="info" size="small" class="ml-2">
            审核意见：{{ row.reviewRemark }}
          </el-text>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="flex justify-end mt-4">
      <el-pagination
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 新建/编辑弹窗 -->
    <ProjectForm v-model:visible="formVisible" :edit-data="editData" @saved="fetchList" />

    <!-- 批量证书弹窗 -->
    <el-dialog v-model="batchDialogVisible" title="批量导出证书" width="440px">
      <p class="text-sm text-gray-600 mb-4">
        将为「<strong>{{ batchProject?.title }}</strong>」中所有已确认打卡的学生生成证书并打包为 ZIP 下载。
      </p>
      <p class="text-xs text-gray-400 mb-2">证书样式为系统标准蓝色版式，自动按服务记录填充内容。</p>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="batchLoading" @click="handleBatchDownload">开始导出</el-button>
      </template>
    </el-dialog>
  </div>
</template>
