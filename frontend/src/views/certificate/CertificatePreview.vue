<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getCertificateDataApi, downloadCertificatePdfApi,
  type CertificateData,
} from '@/api/certificate'
import { generateCertificateTextApi } from '@/api/ai'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const aiLoading = ref(false)
const pdfLoading = ref(false)
const data = ref<CertificateData | null>(null)

// 与后端 cert_pdf_service.py 中 COMMENDATION_TEXT 完全一致 —— 同源默认表彰语
const DEFAULT_COMMENDATION =
  '该同学在本次志愿服务活动中表现优秀，认真履行职责，圆满完成各项任务，' +
  '展现了良好的责任意识与服务精神，特此证明。'

// AI 生成的表彰语（覆盖默认文本，仅前端预览；PDF 始终按默认文本输出）
const aiCommendation = ref('')

const displayCommendation = computed(() => aiCommendation.value || DEFAULT_COMMENDATION)

async function fetchData() {
  const projectId = Number(route.params.projectId)
  if (!projectId) return
  loading.value = true
  try {
    const res = await getCertificateDataApi(projectId)
    data.value = res.data
  } finally {
    loading.value = false
  }
}

async function handleDownloadPdf() {
  if (!data.value) return
  const projectId = Number(route.params.projectId)
  pdfLoading.value = true
  try {
    // 把 AI 表彰语（若有）一起带去后端，让 PDF 与预览保持一致
    await downloadCertificatePdfApi(projectId, undefined, aiCommendation.value || undefined)
    ElMessage.success('证书 PDF 已下载')
  } catch {
    /* 拦截器已提示 */
  } finally {
    pdfLoading.value = false
  }
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
    aiCommendation.value = res.data.text
    ElMessage.success('AI 文案已生成，下载 PDF 时会一并使用')
  } catch {
    ElMessage.error('AI 文案生成失败')
  } finally {
    aiLoading.value = false
  }
}

function formatToday() {
  const d = new Date()
  return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日`
}

onMounted(fetchData)
</script>

<template>
  <div v-loading="loading">
    <!-- 操作栏 -->
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <el-button text @click="router.back()">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <el-button type="success" :loading="pdfLoading" :disabled="pdfLoading" @click="handleDownloadPdf">
        <el-icon><Download /></el-icon> 下载标准 PDF
      </el-button>
      <el-button type="warning" :loading="aiLoading" :disabled="aiLoading" @click="handleAiGenerate">
        <el-icon><MagicStick /></el-icon> AI 生成表彰语
      </el-button>
      <span class="ml-auto text-xs text-gray-400">下方为 PDF 同款实时预览</span>
    </div>

    <!-- 证书内容（横版 A4 比例、双框、与后端 PDF 视觉 1:1 对齐） -->
    <div v-if="data" class="cert-page mx-auto">
      <div class="cert-outer-border">
        <div class="cert-inner-border">
          <!-- 标题 -->
          <h1 class="cert-title">志愿服务证明</h1>
          <div class="cert-title-bar"></div>

          <!-- 正文：事实段（连续段落，自动换行） + 表彰语段 -->
          <div class="cert-body">
            <p class="cert-fact">
              兹证明 <strong>{{ data.userName }}</strong> 同学（学号：{{ data.studentId }}），系
              {{ data.college }} {{ data.major }} 专业学生，于 {{ data.signInTime }} 参加了
              "<strong>{{ data.projectTitle }}</strong>" 志愿服务活动，累计服务时长
              <strong>{{ data.durationHours }}</strong> 小时。
            </p>
            <p class="cert-commendation">{{ displayCommendation }}</p>
          </div>

          <!-- 右下角签发单位 + 盖章占位 -->
          <div class="cert-footer">
            <div class="cert-text-block">
              <div class="cert-signature">高校青年志愿者服务中心</div>
              <div class="cert-date">{{ formatToday() }}</div>
            </div>
            <div class="cert-stamp">盖章处</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 横版 A4 比例 1.414:1，与 reportlab 端 pagesize=landscape(A4) 同源 */
.cert-page {
  width: 842px;
  height: 595px;
  position: relative;
  background: #F8FAFB;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
}
.cert-outer-border {
  position: absolute;
  inset: 30px;
  border: 3px solid #4F6EF7;
}
.cert-inner-border {
  position: absolute;
  inset: 10px;
  border: 1px solid #4F6EF7;
  padding: 70px 110px 0 110px;
  font-family: 'SimSun', '宋体', 'Songti SC', serif;
  color: #333;
}
.cert-title {
  text-align: center;
  font-size: 36px;
  font-weight: bold;
  font-family: 'SimHei', '黑体', 'Heiti SC', sans-serif;
  letter-spacing: 6px;
  margin: 0 0 10px 0;
  color: #4F6EF7;
}
.cert-title-bar {
  width: 160px;
  height: 3px;
  background: #4F6EF7;
  margin: 0 auto 36px auto;
}
.cert-body {
  font-size: 14px;
}
.cert-body p {
  margin: 0;
}
.cert-body strong {
  font-weight: bold;
  color: #111;
}
.cert-fact {
  line-height: 30px;
  text-align: justify;
}
.cert-commendation {
  margin-top: 14px !important;
  font-size: 13px;
  line-height: 24px;
  text-align: justify;
}
.cert-footer {
  position: absolute;
  right: 110px;
  bottom: 80px;
  display: flex;
  align-items: center;
  gap: 24px;
}
.cert-text-block {
  text-align: left;
}
.cert-signature {
  font-family: 'SimHei', '黑体', 'Heiti SC', sans-serif;
  font-size: 14px;
  margin-bottom: 8px;
  color: #4F6EF7;
}
.cert-date {
  color: #666;
  font-size: 12px;
}
.cert-stamp {
  width: 72px;
  height: 72px;
  border: 1.5px dashed #4F6EF7;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  color: #4F6EF7;
  font-family: 'SimHei', '黑体', 'Heiti SC', sans-serif;
}
</style>
