<script setup lang="ts">
import { ref, computed, onMounted, markRaw, watch } from 'vue'
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
  drillStatsApi,
  type OverviewStats, type StatisticsFilter, type DrillItem, type DrillDimension,
} from '@/api/statistics'
import { getCollegeListApi, type CollegeItem } from '@/api/college'
import { nlQueryStreamApi, type ChartData } from '@/api/ai'
import type { EChartsOption } from 'echarts'

// 注册 ECharts 组件
use([CanvasRenderer, PieChart, BarChart, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const loading = ref(false)
const overview = ref<OverviewStats>({ projectCount: 0, volunteerCount: 0, totalHours: 0, applicationCount: 0 })

// ========== 筛选 ==========
const dateRange = ref<[string, string] | null>(null)
const filterCollege = ref<number | undefined>(undefined)
const filterCategory = ref('')
const collegeList = ref<CollegeItem[]>([])
const CATEGORY_OPTIONS = ['环保', '支教', '社区帮扶', '赛事服务', '医疗健康', '科技推广', '文化宣传', '其他']

const currentFilter = computed<StatisticsFilter>(() => ({
  startDate: dateRange.value?.[0] || undefined,
  endDate: dateRange.value?.[1] || undefined,
  collegeId: filterCollege.value,
  category: filterCategory.value || undefined,
}))

function handleResetFilter() {
  dateRange.value = null
  filterCollege.value = undefined
  filterCategory.value = ''
}

// ========== 图表配置 ==========
const categoryOption = ref<EChartsOption>({})
const collegeOption = ref<EChartsOption>({})
const monthlyOption = ref<EChartsOption>({})
const applicationOption = ref<EChartsOption>({})

async function fetchData() {
  loading.value = true
  try {
    const f = currentFilter.value
    const [overviewRes, categoryRes, collegeRes, monthlyRes, appRes] = await Promise.all([
      getOverviewApi(f),
      getCategoryStatsApi(f),
      getCollegeStatsApi(f),
      getMonthlyHoursApi(f),
      getApplicationStatsApi(f),
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

// ========== 下钻 ==========
const drillVisible = ref(false)
const drillTitle = ref('')
const drillLoading = ref(false)
const drillItems = ref<DrillItem[]>([])

async function openDrill(dimension: DrillDimension, value: string, label: string) {
  if (!value) return
  drillVisible.value = true
  drillTitle.value = label
  drillLoading.value = true
  drillItems.value = []
  try {
    const res = await drillStatsApi(dimension, value, currentFilter.value)
    drillItems.value = res.data
  } finally {
    drillLoading.value = false
  }
}

function onCategoryChartClick(params: { name?: string }) {
  if (params?.name) openDrill('category', params.name, `项目类型「${params.name}」明细`)
}
function onCollegeChartClick(params: { name?: string }) {
  if (params?.name) openDrill('college', params.name, `学院「${params.name}」明细`)
}
function onMonthlyChartClick(params: { name?: string }) {
  if (params?.name) openDrill('month', params.name, `${params.name} 月度明细`)
}
function onApplicationChartClick(params: { name?: string }) {
  if (params?.name) ElMessage.info(`项目「${params.name}」可在项目管理页查看详情`)
}

// ========== 导出（带筛选） ==========
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

// 筛选条件变化时自动刷新
watch([dateRange, filterCollege, filterCategory], () => {
  fetchData()
})

onMounted(async () => {
  const colRes = await getCollegeListApi()
  collegeList.value = colRes.data
  await fetchData()
})
</script>

<template>
  <div v-loading="loading">
    <h2 class="text-xl font-bold text-gray-800 mb-4">统计报表</h2>

    <!-- 筛选区 -->
    <el-card shadow="never" class="mb-4">
      <div class="flex flex-wrap items-center gap-3">
        <span class="text-sm text-gray-500">筛选条件：</span>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="default"
          style="width: 280px"
        />
        <el-select v-model="filterCollege" placeholder="按学院筛选" clearable style="width: 180px">
          <el-option v-for="c in collegeList" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-select v-model="filterCategory" placeholder="按项目类型筛选" clearable style="width: 180px">
          <el-option v-for="cat in CATEGORY_OPTIONS" :key="cat" :label="cat" :value="cat" />
        </el-select>
        <el-button text type="info" @click="handleResetFilter">重置</el-button>
        <el-tag v-if="dateRange || filterCollege || filterCategory" type="success" size="small">已应用筛选</el-tag>
        <span class="ml-auto text-xs text-gray-400">点击图表可下钻查看明细</span>
      </div>
    </el-card>

    <!-- 总览卡片 -->
    <el-row :gutter="16" class="mb-6">
      <el-col :xs="12" :sm="12" :lg="6" class="mb-4 lg:mb-0">
        <div class="bg-white rounded-xl p-5 card-hover border border-gray-100">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center bg-blue-50 text-blue-500 flex-shrink-0">
              <el-icon size="24"><Tickets /></el-icon>
            </div>
            <div>
              <div class="text-xs text-gray-400">项目总数</div>
              <div class="text-2xl font-bold text-gray-800" style="font-variant-numeric: tabular-nums;">{{ overview.projectCount }}</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="12" :lg="6" class="mb-4 lg:mb-0">
        <div class="bg-white rounded-xl p-5 card-hover border border-gray-100">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center bg-green-50 text-green-500 flex-shrink-0">
              <el-icon size="24"><User /></el-icon>
            </div>
            <div>
              <div class="text-xs text-gray-400">志愿者人数</div>
              <div class="text-2xl font-bold text-gray-800" style="font-variant-numeric: tabular-nums;">{{ overview.volunteerCount }}</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="12" :lg="6" class="mb-4 lg:mb-0">
        <div class="bg-white rounded-xl p-5 card-hover border border-gray-100">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center bg-orange-50 text-orange-500 flex-shrink-0">
              <el-icon size="24"><Clock /></el-icon>
            </div>
            <div>
              <div class="text-xs text-gray-400">累计服务时长</div>
              <div class="text-2xl font-bold text-gray-800" style="font-variant-numeric: tabular-nums;">{{ overview.totalHours }}h</div>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="12" :lg="6" class="mb-4 lg:mb-0">
        <div class="bg-white rounded-xl p-5 card-hover border border-gray-100">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center bg-purple-50 text-purple-500 flex-shrink-0">
              <el-icon size="24"><DataAnalysis /></el-icon>
            </div>
            <div>
              <div class="text-xs text-gray-400">报名总数</div>
              <div class="text-2xl font-bold text-gray-800" style="font-variant-numeric: tabular-nums;">{{ overview.applicationCount }}</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域（支持点击下钻） -->
    <el-row :gutter="16" class="mb-6">
      <el-col :xs="24" :md="12" class="mb-4 md:mb-0">
        <el-card shadow="never">
          <v-chart :option="categoryOption" style="height: 350px" autoresize @click="onCategoryChartClick" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <v-chart :option="collegeOption" style="height: 350px" autoresize @click="onCollegeChartClick" />
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="16" class="mb-6">
      <el-col :xs="24" :md="12" class="mb-4 md:mb-0">
        <el-card shadow="never">
          <v-chart :option="monthlyOption" style="height: 350px" autoresize @click="onMonthlyChartClick" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <v-chart :option="applicationOption" style="height: 350px" autoresize @click="onApplicationChartClick" />
        </el-card>
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

    <!-- 下钻明细弹窗 -->
    <el-dialog v-model="drillVisible" :title="drillTitle" width="820px">
      <div v-loading="drillLoading">
        <el-table :data="drillItems" stripe size="small" max-height="480">
          <el-table-column prop="projectTitle" label="项目名称" min-width="180" show-overflow-tooltip />
          <el-table-column prop="category" label="类型" width="100" />
          <el-table-column label="状态" width="90" align="center">
            <template #default="{ row }">
              <el-tag size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="起止时间" width="180">
            <template #default="{ row }">
              <span class="text-xs text-gray-500">
                {{ row.startTime?.slice(0, 10) || '-' }} ~ {{ row.endTime?.slice(0, 10) || '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="approvedCount" label="录取人数" width="90" align="center" />
          <el-table-column prop="confirmedCount" label="签到人次" width="90" align="center" />
          <el-table-column prop="totalHours" label="累计时长(h)" width="110" align="center" />
        </el-table>
        <el-empty v-if="!drillLoading && drillItems.length === 0" description="无明细数据" :image-size="80" />
      </div>
    </el-dialog>
  </div>
</template>
