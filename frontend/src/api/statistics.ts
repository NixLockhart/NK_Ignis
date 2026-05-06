import request from './request'

export interface OverviewStats {
  projectCount: number
  volunteerCount: number
  totalHours: number
  applicationCount: number
}

export interface CategoryStats {
  categories: string[]
  counts: number[]
}

export interface CollegeStats {
  colleges: string[]
  counts: number[]
}

export interface MonthlyHoursTrend {
  months: string[]
  hours: number[]
}

export interface ApplicationStats {
  projects: string[]
  counts: number[]
}

export interface StatisticsFilter {
  startDate?: string
  endDate?: string
  collegeId?: number
  category?: string
}

export interface DrillItem {
  projectId: number
  projectTitle: string
  category: string
  status: string
  startTime: string | null
  endTime: string | null
  approvedCount: number
  confirmedCount: number
  totalHours: number
}

export type DrillDimension = 'college' | 'category' | 'month'

function paramsOf(filter?: StatisticsFilter) {
  if (!filter) return undefined
  const out: Record<string, string | number> = {}
  if (filter.startDate) out.startDate = filter.startDate
  if (filter.endDate) out.endDate = filter.endDate
  if (filter.collegeId) out.collegeId = filter.collegeId
  if (filter.category) out.category = filter.category
  return out
}

export function getOverviewApi(filter?: StatisticsFilter) {
  return request.get('/statistics/overview', { params: paramsOf(filter) })
}

export function getCategoryStatsApi(filter?: StatisticsFilter) {
  return request.get('/statistics/category', { params: paramsOf(filter) })
}

export function getCollegeStatsApi(filter?: StatisticsFilter) {
  return request.get('/statistics/college', { params: paramsOf(filter) })
}

export function getMonthlyHoursApi(filter?: StatisticsFilter) {
  return request.get('/statistics/monthly-hours', { params: paramsOf(filter) })
}

export function getApplicationStatsApi(filter?: StatisticsFilter) {
  return request.get('/statistics/applications', { params: paramsOf(filter) })
}

export function drillStatsApi(dimension: DrillDimension, value: string, filter?: StatisticsFilter) {
  const params = { dimension, value, ...(paramsOf(filter) || {}) }
  return request.get('/statistics/drill', { params })
}

export interface DashboardCard {
  title: string
  value: number
  unit: string
  color: string
}

export interface DashboardStats {
  cards: DashboardCard[]
}

export function getDashboardApi() {
  return request.get('/statistics/dashboard')
}

// 导出函数（blob 下载）
function downloadFile(url: string, params?: Record<string, unknown>) {
  return request.get(url, {
    params,
    responseType: 'blob',
  }).then((res: any) => {
    const blob = new Blob([res.data])
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    // 尝试从响应头获取文件名（兼容 filename*=UTF-8''xxx 和 filename="xxx" 两种格式）
    const disposition = res.headers?.['content-disposition'] || ''
    const starMatch = disposition.match(/filename\*=UTF-8''(.+?)(?:;|$)/)
    const plainMatch = disposition.match(/filename="?([^";]+)"?/)
    const filename = starMatch?.[1] || plainMatch?.[1] || ''
    link.download = filename ? decodeURIComponent(filename) : 'export.xlsx'
    link.click()
    URL.revokeObjectURL(link.href)
  })
}

export function exportApplicationsApi(projectId: number) {
  return downloadFile('/export/applications', { projectId })
}

export function exportProjectStatsApi() {
  return downloadFile('/export/project-stats')
}

export function exportHoursRecordsApi() {
  return downloadFile('/export/hours-records')
}
