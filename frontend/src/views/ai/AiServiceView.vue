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

// ========== Tab 3: 自然语言查询（生成式UI） ==========
interface NlSegment {
  kind: 'text' | 'chart'
  content: string
  chartData?: ChartData
  chartOption?: EChartsOption
}

const nlInput = ref('')
const nlLoading = ref(false)
const nlSegments = ref<NlSegment[]>([])
const nlStatus = ref('')

async function handleNlQuery() {
  const question = nlInput.value.trim()
  if (!question || nlLoading.value) return

  nlLoading.value = true
  nlSegments.value = []
  nlStatus.value = '正在连接...'

  await nlQueryStreamApi(
    question,
    (text) => {
      nlStatus.value = ''
      const segs = nlSegments.value
      if (segs.length === 0 || segs[segs.length - 1].kind !== 'text') {
        segs.push({ kind: 'text', content: text })
      } else {
        segs[segs.length - 1].content += text
      }
      nlSegments.value = [...segs]
    },
    (chart) => {
      nlSegments.value = [
        ...nlSegments.value,
        { kind: 'chart', content: '', chartData: chart, chartOption: markRaw(buildChartOption(chart)) },
      ]
    },
    () => { nlLoading.value = false; nlStatus.value = '' },
    (err) => {
      nlSegments.value = [{ kind: 'text', content: `查询失败：${err}` }]
      nlLoading.value = false
      nlStatus.value = ''
    },
    (status) => { nlStatus.value = status },
  )
}

// ECharts 配置生成（兼容 Dify Agent 输出的 xAxis/series 格式和旧版 labels/values 格式）
function buildChartOption(chart: ChartData): EChartsOption {
  const baseTitle = { text: chart.title, left: 'center' as const, textStyle: { fontSize: 14 } }

  if (chart.type === 'pie') {
    let pieData: Array<{ name: string; value: number }> = []
    if (chart.labels && chart.values) {
      pieData = chart.labels.map((l, i) => ({ name: l, value: chart.values![i] }))
    } else if (chart.series?.[0]?.data) {
      pieData = chart.series[0].data as Array<{ name: string; value: number }>
    }
    return {
      title: baseTitle,
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [{ type: 'pie', radius: '60%', data: pieData }],
    }
  }

  // bar / line
  const xAxisData = chart.xAxis || chart.labels || []
  const seriesArr = chart.series?.map((s) => ({
    type: chart.type as 'bar' | 'line',
    name: s.name,
    data: s.data,
    ...(chart.type === 'line' ? { smooth: true, areaStyle: { opacity: 0.15 } } : {}),
    ...(chart.type === 'bar' ? { itemStyle: { borderRadius: [4, 4, 0, 0] } } : {}),
  })) || [{
    type: chart.type as 'bar' | 'line',
    data: chart.values || [],
    ...(chart.type === 'line' ? { smooth: true, areaStyle: { opacity: 0.15 } } : {}),
    ...(chart.type === 'bar' ? { itemStyle: { borderRadius: [4, 4, 0, 0] } } : {}),
  }]

  return {
    title: baseTitle,
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: xAxisData, axisLabel: { rotate: 30, fontSize: 11 } },
    yAxis: { type: 'value' },
    legend: (seriesArr.length > 1) ? { bottom: 0 } : undefined,
    series: seriesArr,
  }
}

// ========== Tab 4: 项目推荐 ==========
const recLoading = ref(false)
const recList = ref<RecommendItem[]>([])

async function fetchRecommend() {
  recLoading.value = true
  try {
    const res = await getRecommendApi()
    recList.value = res.data
  } catch {
    ElMessage.error('获取推荐失败')
  } finally {
    recLoading.value = false
  }
}

function goProject(projectId: number) {
  router.push(`/project/${projectId}`)
}

function formatTime(time: string | null) {
  if (!time) return '--'
  return time.replace('T', ' ').slice(0, 10)
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
            </template>

            <div
              v-for="(msg, idx) in chatMessages"
              :key="idx"
              class="flex"
              :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
            >
              <div
                class="max-w-[70%] px-4 py-2 rounded-lg text-sm leading-relaxed"
                :class="msg.role === 'user'
                  ? 'bg-blue-500 text-white rounded-br-none'
                  : 'bg-white border border-gray-200 text-gray-700 rounded-bl-none markdown-body'"
              >
                <template v-if="msg.role === 'user'">{{ msg.content }}</template>
                <div v-else v-html="renderMd(msg.content)" />
                <span
                  v-if="msg.role === 'assistant' && chatLoading && idx === chatMessages.length - 1 && msg.content"
                  class="inline-block w-1.5 h-4 bg-gray-400 ml-0.5 animate-pulse align-middle"
                />
              </div>
            </div>

            <div v-if="chatLoading && chatMessages.length > 0 && !chatMessages[chatMessages.length - 1].content" class="flex justify-start">
              <div class="bg-white border border-gray-200 px-4 py-2 rounded-lg rounded-bl-none text-sm text-gray-400">
                AI 正在思考中...
              </div>
            </div>
          </div>

          <div class="text-xs text-gray-400 mb-2">温馨提示：AI回答仅供参考，具体请以学校相关文件为准。</div>

          <div class="flex gap-2">
            <el-input v-model="chatInput" placeholder="请输入您的问题..." :disabled="chatLoading" @keyup.enter="handleSendQuestion" />
            <el-button type="primary" :loading="chatLoading" @click="handleSendQuestion">发送</el-button>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab 2: 证书文案生成 -->
      <el-tab-pane label="证书文案生成">
        <el-form :model="certForm" label-width="100px" class="max-w-[600px]">
          <el-form-item label="志愿者姓名">
            <el-input v-model="certForm.userName" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="项目名称">
            <el-input v-model="certForm.projectTitle" placeholder="请输入项目名称" />
          </el-form-item>
          <el-form-item label="服务时长">
            <el-input-number v-model="certForm.durationHours" :min="0" :precision="2" />
            <span class="ml-2 text-gray-500">小时</span>
          </el-form-item>
          <el-form-item label="活动类型">
            <el-select v-model="certForm.category" placeholder="请选择活动类型">
              <el-option label="环保" value="环保" />
              <el-option label="助教" value="助教" />
              <el-option label="社区服务" value="社区服务" />
              <el-option label="文化活动" value="文化活动" />
              <el-option label="敬老助残" value="敬老助残" />
              <el-option label="其他" value="其他" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="certLoading" @click="handleGenerateText">生成文案</el-button>
          </el-form-item>
        </el-form>

        <div v-if="certResult || certLoading" class="mt-4 max-w-[600px]">
          <div class="flex items-center justify-between mb-2">
            <span class="font-semibold text-gray-700">
              生成结果
              <span v-if="certLoading" class="text-sm text-gray-400 font-normal ml-2">正在生成中...</span>
            </span>
            <el-button v-if="certResult && !certLoading" type="primary" text size="small" @click="handleCopyText">复制文案</el-button>
          </div>
          <el-input v-model="certResult" type="textarea" :rows="6" :readonly="certLoading" placeholder="AI生成的表彰语将显示在这里" />
        </div>
      </el-tab-pane>

      <!-- Tab 3: 智能数据查询（生成式UI） -->
      <el-tab-pane label="智能数据查询">
        <div class="max-w-[900px]">
          <p class="text-sm text-gray-500 mb-4">用自然语言提问，AI 将查询数据库并自动生成可视化图表。</p>

          <div class="flex gap-2 mb-4">
            <el-input v-model="nlInput" placeholder="例如：各学院参与人数排名、服务时长趋势、项目类型分布..." :disabled="nlLoading" @keyup.enter="handleNlQuery" />
            <el-button type="primary" :loading="nlLoading" @click="handleNlQuery">分析</el-button>
          </div>

          <!-- 快捷查询标签 -->
          <div class="flex gap-2 mb-4 flex-wrap">
            <el-tag
              v-for="q in ['各学院参与志愿服务的人数排名', '各类活动的项目数量分布', '每月服务时长趋势如何', '服务时长排名前十的学生', '各项目报名人数对比']"
              :key="q"
              class="cursor-pointer"
              effect="plain"
              @click="nlInput = q; handleNlQuery()"
            >{{ q }}</el-tag>
          </div>

          <!-- 生成式UI：文本段落与图表交替渲染 -->
          <div v-if="nlSegments.length > 0" class="space-y-4 mb-4">
            <template v-for="(seg, idx) in nlSegments" :key="idx">
              <!-- 文本片段（内容为空则隐藏） -->
              <el-card v-if="seg.kind === 'text' && renderMd(seg.content)" shadow="never">
                <template #header>
                  <div class="flex items-center gap-2">
                    <el-icon><DataAnalysis /></el-icon>
                    <span class="font-semibold">AI 数据分析</span>
                    <span v-if="nlLoading && idx === nlSegments.length - 1" class="text-sm text-gray-400 font-normal">正在分析中...</span>
                  </div>
                </template>
                <div class="text-sm text-gray-700 leading-7 markdown-body" v-html="renderMd(seg.content)" />
                <span
                  v-if="nlLoading && idx === nlSegments.length - 1"
                  class="inline-block w-1.5 h-4 bg-gray-400 ml-0.5 animate-pulse align-middle"
                />
              </el-card>
              <!-- 图表片段 -->
              <el-card v-else-if="seg.kind === 'chart' && seg.chartOption" shadow="never">
                <template #header>
                  <div class="flex items-center gap-2">
                    <el-icon><TrendCharts /></el-icon>
                    <span class="text-sm font-semibold text-gray-600">{{ seg.chartData?.title }}</span>
                  </div>
                </template>
                <v-chart :option="seg.chartOption" style="height: 320px;" autoresize />
              </el-card>
            </template>
          </div>

          <!-- 加载状态（尚无内容时显示） -->
          <div v-if="nlLoading && nlSegments.length === 0" class="text-center text-gray-400 py-8">
            <el-icon class="animate-spin" size="24"><Loading /></el-icon>
            <p class="mt-2">{{ nlStatus || '正在分析中...' }}</p>
          </div>

          <el-empty v-if="!nlLoading && nlSegments.length === 0" description="输入问题开始智能分析" />
        </div>
      </el-tab-pane>

      <!-- Tab 4: 项目推荐（仅学生可见） -->
      <el-tab-pane v-if="userStore.role === 'student'" label="项目推荐">
        <div>
          <div class="flex items-center justify-between mb-4">
            <p class="text-sm text-gray-500">根据您的历史参与记录和兴趣偏好，为您推荐以下志愿项目</p>
            <el-button type="primary" :loading="recLoading" @click="fetchRecommend">
              <el-icon><Refresh /></el-icon> 刷新推荐
            </el-button>
          </div>

          <div v-loading="recLoading">
            <el-row :gutter="16" v-if="recList.length > 0">
              <el-col :span="12" v-for="item in recList" :key="item.projectId" class="mb-4">
                <el-card shadow="hover" class="cursor-pointer" @click="goProject(item.projectId)">
                  <div class="flex items-start justify-between mb-2">
                    <span class="font-semibold text-gray-800">{{ item.title }}</span>
                    <el-tag size="small" type="info">{{ item.category || '其他' }}</el-tag>
                  </div>
                  <div class="text-xs text-gray-400 mb-2 space-y-1">
                    <div v-if="item.location"><el-icon><Location /></el-icon> {{ item.location }}</div>
                    <div><el-icon><Calendar /></el-icon> {{ formatTime(item.startTime) }} ~ {{ formatTime(item.endTime) }}</div>
                    <div><el-icon><User /></el-icon> {{ item.creatorName || '--' }} · 招募{{ item.maxPeople }}人</div>
                  </div>
                  <div v-if="item.reason" class="text-sm text-blue-600 bg-blue-50 rounded px-2 py-1">
                    <el-icon><MagicStick /></el-icon> {{ item.reason }}
                  </div>
                </el-card>
              </el-col>
            </el-row>

            <el-empty v-if="!recLoading && recList.length === 0" description="暂无推荐项目，可能当前没有可报名的项目" />
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
