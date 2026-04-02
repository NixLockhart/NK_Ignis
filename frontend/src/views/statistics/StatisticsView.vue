<script setup lang="ts">
import { ref, onMounted, markRaw } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart, LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'
import {
  getOverviewApi, getCategoryStatsApi, getCollegeStatsApi,
  getMonthlyHoursApi, getApplicationStatsApi,
  exportProjectStatsApi, exportHoursRecordsApi,
  type OverviewStats,
} from '@/api/statistics'
import { nlQueryStreamApi, type ChartData } from '@/api/ai'
import type { EChartsOption } from 'echarts'

// 注册 ECharts 组件
use([CanvasRenderer, PieChart, BarChart, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const loading = ref(false)
const overview = ref<OverviewStats>({ projectCount: 0, volunteerCount: 0, totalHours: 0, applicationCount: 0 })

// 图表配置
const categoryOption = ref({})
const collegeOption = ref({})
const monthlyOption = ref({})
const applicationOption = ref({})

async function fetchData() {
  loading.value = true
  try {
    const [overviewRes, categoryRes, collegeRes, monthlyRes, appRes] = await Promise.all([
      getOverviewApi(),
      getCategoryStatsApi(),
      getCollegeStatsApi(),
      getMonthlyHoursApi(),
      getApplicationStatsApi(),
    ])

    overview.value = overviewRes.data

    const cat = categoryRes.data
    categoryOption.value = {
      title: { text: '各类项目数量', left: 'center' },
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0 },
      series: [{ type: 'pie', radius: '60%', data: cat.categories.map((name: string, i: number) => ({ name, value: cat.counts[i] })) }],
    }

    const col = collegeRes.data
    collegeOption.value = {
      title: { text: '各学院参与人数', left: 'center' },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: col.colleges, axisLabel: { rotate: 30 } },
      yAxis: { type: 'value', name: '人数' },
      series: [{ type: 'bar', data: col.counts, itemStyle: { color: '#409EFF' } }],
    }

    const mon = monthlyRes.data
    monthlyOption.value = {
      title: { text: '每月服务时长趋势', left: 'center' },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: mon.months },
      yAxis: { type: 'value', name: '小时' },
      series: [{ type: 'line', data: mon.hours, smooth: true, areaStyle: { opacity: 0.3 } }],
    }

    const app = appRes.data
    applicationOption.value = {
      title: { text: '各项目报名人数', left: 'center' },
      tooltip: { trigger: 'axis' },
      grid: { bottom: 80 },
      xAxis: { type: 'category', data: app.projects, axisLabel: { rotate: 45, fontSize: 11 } },
      yAxis: { type: 'value', name: '人数' },
      series: [{ type: 'bar', data: app.counts, itemStyle: { color: '#67C23A' } }],
    }
  } finally {
    loading.value = false
  }
}

async function handleExportProjectStats() {
  try { await exportProjectStatsApi(); ElMessage.success('导出成功') } catch { ElMessage.error('导出失败') }
}
async function handleExportHours() {
  try { await exportHoursRecordsApi(); ElMessage.success('导出成功') } catch { ElMessage.error('导出失败') }
}

// ========== AI 智能查询（生成式UI） ==========
function renderMd(text: string): string {
  if (!text) return ''
  const cleaned = text.replace(/\{data-source-line="[^"]*"\}/g, '').trim()
  if (!cleaned) return ''
  return marked.parse(cleaned, { breaks: true }) as string
}

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
      nlLoading.value = false; nlStatus.value = ''
    },
    (status) => { nlStatus.value = status },
  )
}

function buildChartOption(chart: ChartData): EChartsOption {
  const baseTitle = { text: chart.title, left: 'center' as const, textStyle: { fontSize: 14 } }
  if (chart.type === 'pie') {
    let pieData: Array<{ name: string; value: number }> = []
    if (chart.labels && chart.values) pieData = chart.labels.map((l, i) => ({ name: l, value: chart.values![i] }))
    else if (chart.series?.[0]?.data) pieData = chart.series[0].data as Array<{ name: string; value: number }>
    return { title: baseTitle, tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' }, series: [{ type: 'pie', radius: '60%', data: pieData }] }
  }
  const xAxisData = chart.xAxis || chart.labels || []
  const seriesArr = chart.series?.map((s) => ({
    type: chart.type as 'bar' | 'line', name: s.name, data: s.data,
    ...(chart.type === 'line' ? { smooth: true, areaStyle: { opacity: 0.15 } } : {}),
    ...(chart.type === 'bar' ? { itemStyle: { borderRadius: [4, 4, 0, 0] } } : {}),
  })) || [{
    type: chart.type as 'bar' | 'line', data: chart.values || [],
    ...(chart.type === 'line' ? { smooth: true, areaStyle: { opacity: 0.15 } } : {}),
    ...(chart.type === 'bar' ? { itemStyle: { borderRadius: [4, 4, 0, 0] } } : {}),
  }]
  return {
    title: baseTitle, tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: xAxisData, axisLabel: { rotate: 30, fontSize: 11 } },
    yAxis: { type: 'value' }, legend: seriesArr.length > 1 ? { bottom: 0 } : undefined, series: seriesArr,
  }
}

onMounted(fetchData)
</script>

<template>
  <div v-loading="loading">
    <h2 class="text-xl font-bold text-gray-800 mb-4">统计报表</h2>

    <!-- 总览卡片 -->
    <el-row :gutter="16" class="mb-6">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-sm text-gray-500">项目总数</div>
            <div class="text-3xl font-bold text-blue-500 mt-1">{{ overview.projectCount }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-sm text-gray-500">志愿者人数</div>
            <div class="text-3xl font-bold text-green-500 mt-1">{{ overview.volunteerCount }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-sm text-gray-500">累计服务时长</div>
            <div class="text-3xl font-bold text-orange-500 mt-1">{{ overview.totalHours }}h</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="text-center">
            <div class="text-sm text-gray-500">报名总数</div>
            <div class="text-3xl font-bold text-purple-500 mt-1">{{ overview.applicationCount }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="16" class="mb-6">
      <el-col :span="12">
        <el-card shadow="never"><v-chart :option="categoryOption" style="height: 350px" autoresize /></el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never"><v-chart :option="collegeOption" style="height: 350px" autoresize /></el-card>
      </el-col>
    </el-row>
    <el-row :gutter="16" class="mb-6">
      <el-col :span="12">
        <el-card shadow="never"><v-chart :option="monthlyOption" style="height: 350px" autoresize /></el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never"><v-chart :option="applicationOption" style="height: 350px" autoresize /></el-card>
      </el-col>
    </el-row>

    <!-- AI 智能查询 -->
    <el-card shadow="never" class="mb-6">
      <template #header>
        <div class="flex items-center gap-2">
          <el-icon><ChatDotRound /></el-icon>
          <span class="font-semibold">AI 智能查询</span>
          <span class="text-xs text-gray-400 font-normal">用自然语言提问，AI 查询数据库并生成可视化图表</span>
        </div>
      </template>

      <div class="flex gap-2 mb-4">
        <el-input v-model="nlInput" placeholder="例如：各学院参与人数排名、服务时长趋势、项目类型分布..." :disabled="nlLoading" @keyup.enter="handleNlQuery" />
        <el-button type="primary" :loading="nlLoading" @click="handleNlQuery">分析</el-button>
      </div>

      <div class="flex gap-2 mb-4 flex-wrap">
        <el-tag v-for="q in ['各学院参与志愿服务的人数排名', '各类活动的项目数量分布', '每月服务时长趋势如何', '服务时长排名前十的学生', '各项目报名人数对比']" :key="q" class="cursor-pointer" effect="plain" @click="nlInput = q; handleNlQuery()">{{ q }}</el-tag>
      </div>

      <!-- 生成式UI段落 -->
      <div v-if="nlSegments.length > 0" class="space-y-4 mb-4">
        <template v-for="(seg, idx) in nlSegments" :key="idx">
          <el-card v-if="seg.kind === 'text' && renderMd(seg.content)" shadow="never" class="!border-gray-100">
            <template #header>
              <div class="flex items-center gap-2">
                <el-icon><DataAnalysis /></el-icon>
                <span class="font-semibold text-sm">AI 数据分析</span>
                <span v-if="nlLoading && idx === nlSegments.length - 1" class="text-xs text-gray-400 font-normal">分析中...</span>
              </div>
            </template>
            <div class="text-sm text-gray-700 leading-7 markdown-body" v-html="renderMd(seg.content)" />
            <span v-if="nlLoading && idx === nlSegments.length - 1" class="inline-block w-1.5 h-4 bg-gray-400 ml-0.5 animate-pulse align-middle" />
          </el-card>
          <el-card v-else-if="seg.kind === 'chart' && seg.chartOption" shadow="never" class="!border-gray-100">
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

      <div v-if="nlLoading && nlSegments.length === 0" class="text-center text-gray-400 py-6">
        <el-icon class="animate-spin" size="24"><Loading /></el-icon>
        <p class="mt-2 text-sm">{{ nlStatus || '正在分析中...' }}</p>
      </div>

      <el-empty v-if="!nlLoading && nlSegments.length === 0" description="输入问题开始智能分析" :image-size="80" />
    </el-card>

    <!-- 导出按钮 -->
    <el-card shadow="never">
      <template #header><span class="font-semibold">数据导出</span></template>
      <div class="flex gap-4">
        <el-button type="primary" @click="handleExportProjectStats">
          <el-icon><Download /></el-icon> 导出项目统计
        </el-button>
        <el-button type="primary" @click="handleExportHours">
          <el-icon><Download /></el-icon> 导出时长记录
        </el-button>
      </div>
    </el-card>
  </div>
</template>
