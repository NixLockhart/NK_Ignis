<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { createProjectApi, updateProjectApi, type ProjectFormData } from '@/api/project'

const props = defineProps<{
  visible: boolean
  editData: ProjectFormData | null
}>()

const emit = defineEmits<{
  'update:visible': [val: boolean]
  saved: []
}>()

const formRef = ref<FormInstance>()
const loading = ref(false)
const isEdit = ref(false)

const categoryOptions = ['环保', '助教', '社区服务', '文化活动', '敬老助残', '其他']

const form = reactive<ProjectFormData>({
  title: '',
  content: '',
  location: '',
  category: '',
  startTime: '',
  endTime: '',
  registrationDeadline: '',
  maxPeople: 0,
  contact: '',
  notice: '',
})

const rules: FormRules = {
  title: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { max: 200, message: '名称不超过200字', trigger: 'blur' },
  ],
  startTime: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  endTime: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  maxPeople: [
    { required: true, message: '请输入招募人数', trigger: 'blur' },
    { type: 'number', min: 1, message: '招募人数必须大于0', trigger: 'blur' },
  ],
}

// 监听 editData 变更，填充表单
watch(() => props.editData, (data) => {
  if (data) {
    isEdit.value = !!data.id
    Object.assign(form, data)
  } else {
    isEdit.value = false
    Object.assign(form, {
      id: undefined, title: '', content: '', location: '', category: '',
      startTime: '', endTime: '', registrationDeadline: '',
      maxPeople: 0, contact: '', notice: '',
    })
  }
}, { immediate: true })

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  // 时间校验
  if (form.startTime && form.endTime && form.startTime >= form.endTime) {
    ElMessage.error('结束时间必须晚于开始时间')
    return
  }

  loading.value = true
  try {
    if (isEdit.value) {
      await updateProjectApi(form)
      ElMessage.success('更新成功')
    } else {
      await createProjectApi(form)
      ElMessage.success('创建成功')
    }
    emit('update:visible', false)
    emit('saved')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="emit('update:visible', $event)"
    :title="isEdit ? '编辑项目' : '新建项目'"
    width="650px"
    destroy-on-close
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="项目名称" prop="title">
        <el-input v-model="form.title" placeholder="请输入项目名称" maxlength="200" show-word-limit />
      </el-form-item>

      <div class="flex gap-3">
        <el-form-item label="活动类型" prop="category" class="flex-1">
          <el-select v-model="form.category" placeholder="请选择" clearable class="w-full">
            <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="活动地点" class="flex-1">
          <el-input v-model="form.location" placeholder="请输入地点" />
        </el-form-item>
      </div>

      <div class="flex gap-3">
        <el-form-item label="开始时间" prop="startTime" class="flex-1">
          <el-date-picker v-model="form.startTime" type="datetime" placeholder="选择时间" value-format="YYYY-MM-DDTHH:mm:ss" class="!w-full" />
        </el-form-item>
        <el-form-item label="结束时间" prop="endTime" class="flex-1">
          <el-date-picker v-model="form.endTime" type="datetime" placeholder="选择时间" value-format="YYYY-MM-DDTHH:mm:ss" class="!w-full" />
        </el-form-item>
      </div>

      <div class="flex gap-3">
        <el-form-item label="报名截止时间" class="flex-1">
          <el-date-picker v-model="form.registrationDeadline" type="datetime" placeholder="选择时间" value-format="YYYY-MM-DDTHH:mm:ss" class="!w-full" />
        </el-form-item>
        <el-form-item label="招募人数" prop="maxPeople" class="flex-1">
          <el-input-number v-model="form.maxPeople" :min="1" :max="9999" class="!w-full" />
        </el-form-item>
      </div>

      <el-form-item label="活动简介">
        <el-input v-model="form.content" type="textarea" :rows="3" placeholder="请输入活动简介" maxlength="2000" show-word-limit />
      </el-form-item>

      <el-form-item label="联系方式">
        <el-input v-model="form.contact" placeholder="请输入联系方式" />
      </el-form-item>

      <el-form-item label="注意事项">
        <el-input v-model="form.notice" type="textarea" :rows="2" placeholder="请输入注意事项" maxlength="1000" show-word-limit />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">{{ isEdit ? '保存' : '创建' }}</el-button>
    </template>
  </el-dialog>
</template>
