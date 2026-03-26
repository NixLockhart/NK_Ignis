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

export function getOverviewApi() {
  return request.get('/statistics/overview')
}

export function getCategoryStatsApi() {
  return request.get('/statistics/category')
}

export function getCollegeStatsApi() {
  return request.get('/statistics/college')
}

export function getMonthlyHoursApi() {
  return request.get('/statistics/monthly-hours')
}

export function getApplicationStatsApi() {
  return request.get('/statistics/applications')
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
