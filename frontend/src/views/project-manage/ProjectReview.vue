<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getProjectListApi, approveProjectApi, rejectProjectApi, type ProjectInfo } from '@/api/project'

const router = useRouter()
const loading = ref(false)
const projectList = ref<ProjectInfo[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

// 审核弹窗
const reviewVisible = ref(false)
const reviewProject = ref<ProjectInfo | null>(null)
const reviewRemark = ref('')
const reviewLoading = ref(false)

async function fetchList() {
  loading.value = true
  try {
    const res = await getProjectListApi({ status: 'pending', page: page.value, pageSize: pageSize.value })
    projectList.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function openReview(row: ProjectInfo) {
  reviewProject.value = row
  reviewRemark.value = ''
  reviewVisible.value = true
}

async function handleApprove() {
  if (!reviewProject.value) return
  reviewLoading.value = true
  try {
    await approveProjectApi(reviewProject.value.id, reviewRemark.value)
    ElMessage.success('审核通过')
    reviewVisible.value = false
    fetchList()
  } finally {
    reviewLoading.value = false
  }
}

async function handleReject() {
  if (!reviewProject.value) return
  if (!reviewRemark.value.trim()) {
    ElMessage.warning('驳回时请填写审核意见')
    return
  }
  reviewLoading.value = true
  try {
    await rejectProjectApi(reviewProject.value.id, reviewRemark.value)
    ElMessage.success('已驳回')
    reviewVisible.value = false
    fetchList()
  } finally {
    reviewLoading.value = false
  }
}

function goDetail(id: number) {
  router.push(`/project/${id}`)
}

function formatTime(time: string | null) {
  if (!time) return '--'
  return time.replace('T', ' ').slice(0, 16)
}

onMounted(fetchList)
</script>

<template>
  <div>
    <h2 class="text-xl font-bold text-gray-800 mb-4">项目审核</h2>

    <el-table :data="projectList" v-loading="loading" stripe>
      <el-table-column prop="title" label="项目名称" min-width="180">
        <template #default="{ row }">
          <el-link type="primary" @click="goDetail(row.id)">{{ row.title }}</el-link>
        </template>
      </el-table-column>
      <el-table-column prop="category" label="类型" width="100" />
      <el-table-column prop="location" label="地点" width="120" />
      <el-table-column label="活动时间" width="170">
        <template #default="{ row }">{{ formatTime(row.startTime) }}</template>
      </el-table-column>
      <el-table-column label="招募人数" width="90" align="center">
        <template #default="{ row }">{{ row.maxPeople }}</template>
      </el-table-column>
      <el-table-column prop="creatorName" label="发起人" width="100" />
      <el-table-column label="提交时间" width="170">
        <template #default="{ row }">{{ formatTime(row.updatedAt) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" text size="small" @click="openReview(row)">审核</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="flex justify-end mt-4">
      <el-pagination
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="(p: number) => { page = p; fetchList() }"
      />
    </div>

    <!-- 审核弹窗 -->
    <el-dialog v-model="reviewVisible" title="项目审核" width="500px" destroy-on-close>
      <template v-if="reviewProject">
        <el-descriptions :column="1" border size="small" class="mb-4">
          <el-descriptions-item label="项目名称">{{ reviewProject.title }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ reviewProject.category }}</el-descriptions-item>
          <el-descriptions-item label="地点">{{ reviewProject.location }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{ formatTime(reviewProject.startTime) }} ~ {{ formatTime(reviewProject.endTime) }}</el-descriptions-item>
          <el-descriptions-item label="招募人数">{{ reviewProject.maxPeople }} 人</el-descriptions-item>
          <el-descriptions-item label="发起人">{{ reviewProject.creatorName }}</el-descriptions-item>
        </el-descriptions>

        <el-form-item label="审核意见">
          <el-input v-model="reviewRemark" type="textarea" :rows="3" placeholder="请输入审核意见（驳回时必填）" />
        </el-form-item>
      </template>

      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button type="danger" :loading="reviewLoading" @click="handleReject">驳回</el-button>
        <el-button type="primary" :loading="reviewLoading" @click="handleApprove">通过</el-button>
      </template>
    </el-dialog>
  </div>
</template>
