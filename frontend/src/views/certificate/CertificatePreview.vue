<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCertificateDataApi, type CertificateData } from '@/api/certificate'
import { generateCertificateTextApi } from '@/api/ai'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const aiLoading = ref(false)
const data = ref<CertificateData | null>(null)

// 默认表彰语模板（第7周将替换为 AI 生成）
const commendation = ref('')

function generateDefaultText(d: CertificateData) {
  return `${d.userName} 同学在"${d.projectTitle}"志愿服务活动中表现优秀，累计服务 ${d.durationHours} 小时，展现了良好的志愿服务精神和奉献意识，特此证明。`
}

async function fetchData() {
  const projectId = Number(route.params.projectId)
  if (!projectId) return
  loading.value = true
  try {
    const res = await getCertificateDataApi(projectId)
    data.value = res.data
    commendation.value = generateDefaultText(res.data)
  } finally {
    loading.value = false
  }
}

function handlePrint() {
  window.print()
}

async function handleAiGenerate() {
  if (!data.value) return
  aiLoading.value = true
  try {
    const res = await generateCertificateTextApi({
      userName: data.value.userName,
      projectTitle: data.value.projectTitle,
      durationHours: data.value.durationHours,
    })
    commendation.value = res.data.text
    ElMessage.success('AI文案已生成')
  } catch {
    ElMessage.error('AI文案生成失败')
  } finally {
    aiLoading.value = false
  }
}

onMounted(fetchData)
</script>

<template>
  <div v-loading="loading">
    <!-- 操作栏（打印时隐藏） -->
    <div class="mb-4 flex gap-3 print:hidden">
      <el-button text @click="router.back()">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <el-button type="primary" @click="handlePrint">
        <el-icon><Printer /></el-icon> 打印 / 导出PDF
      </el-button>
      <el-button type="warning" :loading="aiLoading" @click="handleAiGenerate">
        <el-icon><MagicStick /></el-icon> AI 生成表彰语
      </el-button>
    </div>

    <!-- 证书内容 -->
    <div v-if="data" class="certificate-page bg-white mx-auto p-12 border border-gray-200" style="width: 800px; min-height: 600px;">
      <!-- 标题 -->
      <div class="text-center mb-10">
        <h1 class="text-3xl font-bold text-gray-800 tracking-widest">志愿服务证明</h1>
        <div class="mt-2 mx-auto" style="width: 200px; height: 3px; background: linear-gradient(to right, #409EFF, #67C23A);"></div>
      </div>

      <!-- 正文 -->
      <div class="text-base leading-8 text-gray-700 px-8">
        <p class="indent-8 mb-6">
          兹证明 <strong class="text-gray-900 underline underline-offset-4 decoration-gray-400 px-1">{{ data.userName }}</strong>
          同学（学号：{{ data.studentId }}，{{ data.college }} {{ data.major }}），
          于 {{ data.signInTime }} 参加了
          <strong class="text-gray-900">"{{ data.projectTitle }}"</strong>
          志愿服务活动，服务时长为
          <strong class="text-blue-600">{{ data.durationHours }}</strong> 小时。
        </p>

        <p class="indent-8 mb-6">{{ commendation }}</p>

        <p class="indent-8">特此证明。</p>
      </div>

      <!-- 底部 -->
      <div class="flex justify-end mt-16 pr-12">
        <div class="text-center">
          <div class="w-28 h-28 border-2 border-dashed border-gray-300 rounded-full flex items-center justify-center mb-2">
            <span class="text-xs text-gray-400">盖章处</span>
          </div>
          <div class="text-sm text-gray-500">高校青年志愿者服务中心</div>
          <div class="text-sm text-gray-400 mt-1">{{ new Date().getFullYear() }}年{{ new Date().getMonth() + 1 }}月{{ new Date().getDate() }}日</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
/* 打印样式 */
@media print {
  body * { visibility: hidden; }
  .certificate-page, .certificate-page * { visibility: visible; }
  .certificate-page {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    border: none !important;
    box-shadow: none !important;
  }
}
</style>
