<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  getCertTemplatesApi, createCertTemplateApi, updateCertTemplateApi, deleteCertTemplateApi,
  type CertTemplate,
} from '@/api/certificate'

const list = ref<CertTemplate[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const editing = ref<CertTemplate | null>(null)

const STYLE_OPTIONS = [
  { value: 'formal', label: '正式' },
  { value: 'warm', label: '温情' },
  { value: 'concise', label: '简洁' },
]

const form = reactive({
  name: '',
  bgColor: '#F8FAFB',
  accentColor: '#4F6EF7',
  signatureText: '高校青年志愿者服务中心',
  commendationStyle: 'formal',
  enabled: true,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  bgColor: [{ required: true, message: '请选择背景色', trigger: 'change' }],
  accentColor: [{ required: true, message: '请选择装饰色', trigger: 'change' }],
  signatureText: [{ required: true, message: '请输入签发单位文本', trigger: 'blur' }],
  commendationStyle: [{ required: true, message: '请选择表彰语风格', trigger: 'change' }],
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getCertTemplatesApi(false)
    list.value = res.data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  Object.assign(form, {
    name: '', bgColor: '#F8FAFB', accentColor: '#4F6EF7',
    signatureText: '高校青年志愿者服务中心', commendationStyle: 'formal', enabled: true,
  })
  dialogVisible.value = true
}

function openEdit(t: CertTemplate) {
  editing.value = t
  Object.assign(form, {
    name: t.name,
    bgColor: t.bgColor,
    accentColor: t.accentColor,
    signatureText: t.signatureText,
    commendationStyle: t.commendationStyle,
    enabled: t.enabled,
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  try {
    if (editing.value) {
      await updateCertTemplateApi(editing.value.id, form)
      ElMessage.success('修改成功')
    } else {
      await createCertTemplateApi(form)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    fetchList()
  } catch {
    /* 拦截器已提示 */
  }
}

async function handleSetDefault(t: CertTemplate) {
  if (t.isDefault) return
  try {
    await updateCertTemplateApi(t.id, { isDefault: true })
    ElMessage.success(`已将「${t.name}」设为默认模板`)
    fetchList()
  } catch {
    /* */
  }
}

async function handleToggleEnabled(t: CertTemplate) {
  try {
    await updateCertTemplateApi(t.id, { enabled: !t.enabled })
    ElMessage.success(t.enabled ? '已停用' : '已启用')
    fetchList()
  } catch {
    /* */
  }
}

async function handleDelete(t: CertTemplate) {
  try {
    await ElMessageBox.confirm(`确认删除模板「${t.name}」？`, '提示', { type: 'warning' })
    await deleteCertTemplateApi(t.id)
    ElMessage.success('删除成功')
    fetchList()
  } catch {
    /* 用户取消或拦截器已提示 */
  }
}

onMounted(fetchList)
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-bold text-gray-800">证书模板管理</h2>
        <p class="text-xs text-gray-500 mt-1">配置证书的颜色、签发单位与表彰语风格，默认模板将用于学生证书下载</p>
      </div>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        <span>新建模板</span>
      </el-button>
    </div>

    <el-card shadow="never" v-loading="loading">
      <el-table :data="list" stripe>
        <el-table-column label="名称" min-width="120">
          <template #default="{ row }">
            <span class="font-semibold">{{ row.name }}</span>
            <el-tag v-if="row.isDefault" type="success" size="small" class="ml-2">默认</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="背景色" width="110">
          <template #default="{ row }">
            <div class="flex items-center gap-2">
              <span class="inline-block w-5 h-5 rounded border border-gray-200" :style="{ background: row.bgColor }"></span>
              <span class="text-xs text-gray-500">{{ row.bgColor }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="装饰色" width="110">
          <template #default="{ row }">
            <div class="flex items-center gap-2">
              <span class="inline-block w-5 h-5 rounded border border-gray-200" :style="{ background: row.accentColor }"></span>
              <span class="text-xs text-gray-500">{{ row.accentColor }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="signatureText" label="签发单位" min-width="180" show-overflow-tooltip />
        <el-table-column prop="commendationStyleLabel" label="表彰语" width="90" align="center" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
              {{ row.enabled ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button v-if="!row.isDefault" text type="success" size="small" @click="handleSetDefault(row)">设为默认</el-button>
            <el-button text :type="row.enabled ? 'warning' : 'success'" size="small" @click="handleToggleEnabled(row)">
              {{ row.enabled ? '停用' : '启用' }}
            </el-button>
            <el-button v-if="!row.isDefault" text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑/新增对话框 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑模板' : '新建模板'" width="540px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="form.name" placeholder="如：经典蓝、暖橙等" />
        </el-form-item>
        <el-form-item label="背景色" prop="bgColor">
          <el-color-picker v-model="form.bgColor" show-alpha />
          <span class="ml-2 text-xs text-gray-500">{{ form.bgColor }}</span>
        </el-form-item>
        <el-form-item label="装饰色" prop="accentColor">
          <el-color-picker v-model="form.accentColor" show-alpha />
          <span class="ml-2 text-xs text-gray-500">{{ form.accentColor }}</span>
        </el-form-item>
        <el-form-item label="签发单位" prop="signatureText">
          <el-input v-model="form.signatureText" />
        </el-form-item>
        <el-form-item label="表彰语风格" prop="commendationStyle">
          <el-select v-model="form.commendationStyle" placeholder="请选择风格">
            <el-option v-for="opt in STYLE_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
