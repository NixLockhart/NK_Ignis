<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getProjectListApi, type ProjectInfo } from '@/api/project'

const router = useRouter()
const loading = ref(false)
const projectList = ref<ProjectInfo[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const filterStatus = ref('')
const filterCategory = ref('')

const statusTagType: Record<string, string> = {
  published: 'success',
  registration_closed: 'warning',
  in_progress: '',
  completed: 'info',
}

const categoryOptions = ['环保', '助教', '社区服务', '文化活动', '敬老助残', '其他']

async function fetchList() {
  loading.value = true
  try {
    const res = await getProjectListApi({
      status: filterStatus.value || undefined,
      category: filterCategory.value || undefined,
      page: page.value,
      pageSize: pageSize.value,
    })
    projectList.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
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

function formatTime(time: string | null) {
  if (!time) return '--'
  return time.replace('T', ' ').slice(0, 16)
}

onMounted(fetchList)
</script>

<template>
  <div>
    <h2 class="text-xl font-bold text-gray-800 mb-4">志愿项目列表</h2>

    <!-- 筛选栏 -->
    <div class="flex gap-3 mb-4">
      <el-select v-model="filterStatus" placeholder="按状态筛选" clearable @change="handleFilter" style="width: 150px">
        <el-option label="已发布" value="published" />
        <el-option label="报名结束" value="registration_closed" />
        <el-option label="进行中" value="in_progress" />
        <el-option label="已结束" value="completed" />
      </el-select>
      <el-select v-model="filterCategory" placeholder="按类型筛选" clearable @change="handleFilter" style="width: 150px">
        <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
      </el-select>
    </div>

    <!-- 项目表格 -->
    <el-table :data="projectList" v-loading="loading" stripe>
      <el-table-column prop="title" label="项目名称" min-width="180">
        <template #default="{ row }">
          <el-link type="primary" @click="goDetail(row.id)">{{ row.title }}</el-link>
        </template>
      </el-table-column>
      <el-table-column prop="category" label="类型" width="100" />
      <el-table-column prop="location" label="地点" width="120" />
      <el-table-column label="活动时间" width="180">
        <template #default="{ row }">
          {{ formatTime(row.startTime) }}
        </template>
      </el-table-column>
      <el-table-column label="招募人数" width="90" align="center">
        <template #default="{ row }">{{ row.maxPeople }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTagType[row.status] || 'info'" size="small">{{ row.statusLabel }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="creatorName" label="发起人" width="100" />
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
  </div>
</template>
