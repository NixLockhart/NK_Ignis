import request from './request'

export interface ApplicationInfo {
  id: number
  projectId: number
  projectTitle: string | null
  userId: number
  userName: string | null
  userStudentId: string | null
  userCollege: string | null
  applyReason: string
  status: string
  statusLabel: string
  applyTime: string | null
  reviewTime: string | null
  reviewRemark: string | null
}

// 报名
export function applyProjectApi(projectId: number, applyReason: string) {
  return request.post('/application/apply', { projectId, applyReason })
}

// 取消报名
export function cancelApplicationApi(id: number) {
  return request.post('/application/cancel', { id })
}

// 通过报名
export function approveApplicationApi(id: number) {
  return request.post('/application/approve', { id })
}

// 拒绝报名
export function rejectApplicationApi(id: number, remark: string) {
  return request.post('/application/reject', { id, remark })
}

// 某项目的报名列表
export function getApplicationListApi(params: { projectId: number; status?: string; page?: number; pageSize?: number }) {
  return request.get('/application/list', { params })
}

// 我的报名记录
export function getMyApplicationsApi(params: { status?: string; page?: number; pageSize?: number }) {
  return request.get('/application/my', { params })
}

// 查询报名状态（用于详情页）
export function getApplicationStatusApi(projectId: number) {
  return request.get('/application/status', { params: { projectId } })
}

// 查询已通过人数
export function getApprovedCountApi(projectId: number) {
  return request.get('/application/count', { params: { projectId } })
}
