<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart, LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { ElMessage } from 'element-plus'
import {
  getOverviewApi, getCategoryStatsApi, getCollegeStatsApi,
  getMonthlyHoursApi, getApplicationStatsApi,
  exportProjectStatsApi, exportHoursRecordsApi,
  type OverviewStats,
} from '@/api/statistics'

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

    // 饼图：各类项目数量
    const cat = categoryRes.data
    categoryOption.value = {
      title: { text: '各类项目数量', left: 'center' },
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0 },
      series: [{
        type: 'pie', radius: '60%',
        data: cat.categories.map((name: string, i: number) => ({ name, value: cat.counts[i] })),
      }],
    }

    // 柱状图：各学院参与人数
    const col = collegeRes.data
    collegeOption.value = {
      title: { text: '各学院参与人数', left: 'center' },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: col.colleges, axisLabel: { rotate: 30 } },
      yAxis: { type: 'value', name: '人数' },
      series: [{ type: 'bar', data: col.counts, itemStyle: { color: '#409EFF' } }],
    }

    // 折线图：每月服务时长趋势
    const mon = monthlyRes.data
    monthlyOption.value = {
      title: { text: '每月服务时长趋势', left: 'center' },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: mon.months },
      yAxis: { type: 'value', name: '小时' },
      series: [{ type: 'line', data: mon.hours, smooth: true, areaStyle: { opacity: 0.3 } }],
    }

    // 柱状图：各项目报名人数
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
  try {
    await exportProjectStatsApi()
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  }
}

async function handleExportHours() {
  try {
    await exportHoursRecordsApi()
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
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
        <el-card shadow="never">
          <v-chart :option="categoryOption" style="height: 350px" autoresize />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <v-chart :option="collegeOption" style="height: 350px" autoresize />
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="16" class="mb-6">
      <el-col :span="12">
        <el-card shadow="never">
          <v-chart :option="monthlyOption" style="height: 350px" autoresize />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <v-chart :option="applicationOption" style="height: 350px" autoresize />
        </el-card>
      </el-col>
    </el-row>

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
