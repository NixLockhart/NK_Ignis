<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getCollegeListApi, createCollegeApi, updateCollegeApi, deleteCollegeApi, type CollegeItem } from '@/api/college'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const list = ref<CollegeItem[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const formData = ref({ name: '', sortOrder: 0 })

async function fetchList() {
  loading.value = true
  try { const res = await getCollegeListApi(); list.value = res.data } finally { loading.value = false }
}

function openAdd() {
  editingId.value = null
  formData.value = { name: '', sortOrder: 0 }
  dialogVisible.value = true
}

function openEdit(item: CollegeItem) {
  editingId.value = item.id
  formData.value = { name: item.name, sortOrder: item.sortOrder }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formData.value.name.trim()) { ElMessage.warning('请输入学院名称'); return }
  try {
    if (editingId.value) {
      await updateCollegeApi(editingId.value, formData.value)
      ElMessage.success('修改成功')
    } else {
      await createCollegeApi(formData.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    fetchList()
  } catch { /* 错误已在拦截器处理 */ }
}

async function handleDelete(item: CollegeItem) {
  await ElMessageBox.confirm(`确定删除「${item.name}」？`, '提示', { type: 'warning' })
  try {
    await deleteCollegeApi(item.id)
    ElMessage.success('删除成功')
    fetchList()
  } catch { /* 错误已在拦截器处理 */ }
}

onMounted(fetchList)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-xl font-bold text-gray-800 m-0">学院管理</h2>
      <el-button type="primary" @click="openAdd"><el-icon><Plus /></el-icon> 添加学院</el-button>
    </div>

    <el-table :data="list" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="学院名称" />
      <el-table-column prop="sortOrder" label="排序" width="100" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" text size="small" @click="openEdit(row)">编辑</el-button>
          <el-button type="danger" text size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑学院' : '添加学院'" width="400px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item label="学院名称">
          <el-input v-model="formData.name" placeholder="请输入学院名称" />
        </el-form-item>
        <el-form-item label="排序序号">
          <el-input-number v-model="formData.sortOrder" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
