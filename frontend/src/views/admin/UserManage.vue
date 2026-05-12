<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getUserListApi, changeRoleApi, resetPasswordApi, type UserInfo } from '@/api/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const userList = ref<UserInfo[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterRole = ref('')
const keyword = ref('')

const roleOptions = [
  { label: '学生', value: 'student' },
  { label: '志愿负责人', value: 'leader' },
  { label: '管理员', value: 'admin' },
]

const roleMap: Record<string, string> = {
  student: '学生',
  leader: '志愿负责人',
  admin: '管理员',
}

const roleTagType: Record<string, string> = {
  student: 'primary',
  leader: 'warning',
  admin: 'danger',
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getUserListApi({
      page: page.value,
      pageSize: pageSize.value,
      role: filterRole.value || undefined,
      keyword: keyword.value || undefined,
    })
    userList.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function handleChangeRole(userId: number, username: string, newRole: string) {
  try {
    await ElMessageBox.confirm(
      `确定将用户 "${username}" 的角色修改为 "${roleMap[newRole]}"？`,
      '确认修改',
      { type: 'warning' },
    )
    await changeRoleApi(userId, newRole)
    ElMessage.success('角色修改成功')
    fetchList()
  } catch {
    // 用户取消或请求失败
  }
}

async function handleResetPassword(userId: number, username: string) {
  try {
    await ElMessageBox.confirm(
      `确定将用户 "${username}" 的密码重置为初始密码 "123456"？请提醒用户登录后及时修改。`,
      '确认重置密码',
      { type: 'warning', confirmButtonText: '重置', cancelButtonText: '取消' },
    )
    const res = await resetPasswordApi(userId)
    ElMessage.success(`已重置为：${res.data.newPassword}`)
  } catch {
    // 用户取消或请求失败
  }
}

function handleFilter() {
  page.value = 1
  fetchList()
}

function handlePageChange(p: number) {
  page.value = p
  fetchList()
}

onMounted(fetchList)
</script>

<template>
  <div>
    <h2 class="text-xl font-bold text-gray-800 mb-4">用户管理</h2>

    <!-- 筛选栏 -->
    <div class="flex gap-3 mb-4">
      <el-input v-model="keyword" placeholder="搜索用户名/姓名/学号" clearable style="width: 220px" @clear="handleFilter" @keyup.enter="handleFilter" />
      <el-select v-model="filterRole" placeholder="按角色筛选" clearable @change="handleFilter" style="width: 150px">
        <el-option v-for="r in roleOptions" :key="r.value" :label="r.label" :value="r.value" />
      </el-select>
      <el-button type="primary" @click="handleFilter">搜索</el-button>
    </div>

    <!-- 用户表格 -->
    <el-table :data="userList" v-loading="loading" stripe>
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="realName" label="姓名" width="100" />
      <el-table-column prop="studentId" label="学号" width="120" />
      <el-table-column prop="college" label="学院" width="150" />
      <el-table-column prop="major" label="专业" width="150" />
      <el-table-column prop="phone" label="手机号" width="130" />
      <el-table-column label="角色" width="120" align="center">
        <template #default="{ row }">
          <el-tag :type="roleTagType[row.role] || 'info'" size="small">{{ roleMap[row.role] || row.role }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="注册时间" width="160">
        <template #default="{ row }">
          {{ row.createdAt ? row.createdAt.replace('T', ' ').slice(0, 16) : '--' }}
        </template>
      </el-table-column>
      <el-table-column label="角色操作" width="160">
        <template #default="{ row }">
          <el-select
            v-if="row.username !== 'admin'"
            :model-value="row.role"
            size="small"
            @change="(val: string) => handleChangeRole(row.id, row.username, val)"
          >
            <el-option v-for="r in roleOptions" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
          <span v-else class="text-xs text-gray-400">超级管理员</span>
        </template>
      </el-table-column>
      <el-table-column label="密码" width="110" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.username !== 'admin'"
            type="warning"
            text
            size="small"
            @click="handleResetPassword(row.id, row.username)"
          >
            重置密码
          </el-button>
          <span v-else class="text-xs text-gray-400">--</span>
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
  </div>
</template>
