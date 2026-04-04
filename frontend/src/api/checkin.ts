import request from './request'

export interface CheckinInfo {
  id: number
  projectId: number
  projectTitle: string | null
  userId: number
  userName: string | null
  userStudentId: string | null
  signInTime: string | null
  signOutTime: string | null
  durationHours: number | null
  status: string
  statusLabel: string
  isAbnormal: boolean
  remark: string | null
  checkedBy: number | null
  checkerName: string | null
  checkedTime: string | null
}

export interface HoursDetail {
  projectId: number
  projectTitle: string | null
  durationHours: number | null
  signInTime: string | null
  signOutTime: string | null
}

// 签到
export function signInApi(projectId: number) {
  return request.post('/checkin/sign-in', { projectId })
}

// 签退
export function signOutApi(projectId: number) {
  return request.post('/checkin/sign-out', { projectId })
}

// 确认打卡
export function confirmCheckinApi(id: number) {
  return request.post('/checkin/confirm', { id })
}

// 驳回打卡
export function rejectCheckinApi(id: number, remark: string) {
  return request.post('/checkin/reject', { id, remark })
}

export function batchConfirmCheckinApi(ids: number[]) {
  return request.post('/checkin/batch-confirm', { ids })
}

export function batchRejectCheckinApi(ids: number[], remark: string) {
  return request.post('/checkin/batch-reject', { ids, remark })
}

// 某项目打卡列表
export function getCheckinListApi(params: { projectId: number; status?: string; page?: number; pageSize?: number }) {
  return request.get('/checkin/list', { params })
}

// 我的打卡记录
export function getMyCheckinsApi(params: { page?: number; pageSize?: number }) {
  return request.get('/checkin/my', { params })
}

// 累计已确认时长
export function getTotalHoursApi(userId?: number) {
  return request.get('/checkin/total-hours', { params: userId ? { userId } : {} })
}

// 各项目时长明细
export function getHoursDetailApi(userId?: number) {
  return request.get('/checkin/hours-detail', { params: userId ? { userId } : {} })
}

// 查询打卡状态
export function getCheckinStatusApi(projectId: number) {
  return request.get('/checkin/status', { params: { projectId } })
}
