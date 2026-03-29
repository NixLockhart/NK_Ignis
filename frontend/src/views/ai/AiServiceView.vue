<script setup lang="ts">
import { ref, reactive, computed, nextTick, onMounted, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart, LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { marked } from 'marked'

// 注册 ECharts 组件
use([CanvasRenderer, PieChart, BarChart, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])
import {
  policyQaStreamApi,
  generateCertificateTextStreamApi,
  nlQueryStreamApi,
  getRecommendApi,
  type ChartData,
  type RecommendItem,
} from '@/api/ai'
import type { EChartsOption } from 'echarts'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

// Markdown 渲染（过滤 Dify 元数据属性）
function renderMd(text: string): string {
  if (!text) return ''
  const cleaned = text.replace(/\{data-source-line="[^"]*"\}/g, '').trim()
  if (!cleaned) return ''
  return marked.parse(cleaned, { breaks: true }) as string
}

// ========== Tab 1: 政策问答 ==========
interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

const chatMessages = ref<ChatMessage[]>([])
const chatInput = ref('')
const chatLoading = ref(false)
const chatAreaRef = ref<HTMLElement>()

async function handleSendQuestion() {
  const question = chatInput.value.trim()
  if (!question || chatLoading.value) return

  chatMessages.value.push({ role: 'user', content: question })
  chatInput.value = ''
  chatLoading.value = true

  const aiMsg: ChatMessage = { role: 'assistant', content: '' }
  chatMessages.value.push(aiMsg)

  await nextTick()
  scrollToBottom()

  await policyQaStreamApi(
    question,
    (chunk) => {
      aiMsg.content += chunk
      chatMessages.value = [...chatMessages.value]
      nextTick(scrollToBottom)
    },
    () => {
      chatLoading.value = false
      if (!aiMsg.content) {
        aiMsg.content = '未获取到回答，请稍后重试。'
        chatMessages.value = [...chatMessages.value]
      }
    },
    (err) => {
      aiMsg.content = `请求失败：${err}`
      chatMessages.value = [...chatMessages.value]
      chatLoading.value = false
    },
  )
}

function scrollToBottom() {
  if (chatAreaRef.value) {
    chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
  }
}

// ========== Tab 2: 证书文案生成 ==========
const certForm = reactive({
  userName: '',
  projectTitle: '',
  durationHours: 0,
  category: '',
})
const certResult = ref('')
const certLoading = ref(false)

async function handleGenerateText() {
  if (!certForm.userName || !certForm.projectTitle) {
    ElMessage.warning('请填写姓名和项目名称')
    return
  }
  if (certLoading.value) return

  certLoading.value = true
  certResult.value = ''

  await generateCertificateTextStreamApi(
    certForm,
    (chunk) => { certResult.value += chunk },
    () => {
      certLoading.value = false
      if (!certResult.value) certResult.value = '未生成文案，请稍后重试。'
    },
    (err) => {
      certResult.value = `生成失败：${err}`
      certLoading.value = false
    },
  )
}

function handleCopyText() {
  if (!certResult.value) return
  navigator.clipboard.writeText(certResult.value).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败，请手动选择复制')
  })
}
</script>

<template>
  <div>
    <h2 class="text-xl font-bold text-gray-800 mb-4">AI 智能服务</h2>

    <el-tabs type="border-card">
      <!-- Tab 1: 智能政策问答 -->
      <el-tab-pane label="智能政策问答">
        <div class="flex flex-col" style="height: 500px;">
          <div ref="chatAreaRef" class="flex-1 overflow-y-auto p-4 bg-gray-50 rounded mb-3 space-y-3">
            <template v-if="chatMessages.length === 0">
              <div class="text-center text-gray-400 mt-20">
                <el-icon size="48"><ChatDotRound /></el-icon>
                <p class="mt-2">请输入您的问题，AI将为您解答志愿服务相关政策</p>
              </div>
            </template    >
