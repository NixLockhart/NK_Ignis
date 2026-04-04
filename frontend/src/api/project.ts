import request from './request'

export interface ProjectInfo {
  id: number
  title: string
  content: string
  location: string
  category: string
  startTime: string | null
  endTime: string | null
  registrationDeadline: string | null
  maxPeople: number
  status: string
  statusLabel: string
  contact: string
  notice: string
  reviewRemark: string | null
  creatorId: number
  creatorName: string | null
  createdAt: string | null
  updatedAt: string | null
}

export interface ProjectListResult {
  list: ProjectInfo[]
  total: number
  page: number
  pageSize: number
}

export interface ProjectFormData {
  id?: number
  title: string
  content: string
  location: string
  category: string
  startTime: string
  endTime: string
  registrationDeadline: string
  maxPeople: number
  contact: string
  notice: string
}

// 创建项目
export function createProjectApi(data: ProjectFormData) {
  return request.post('/project/create', data)
}

// 编辑项目
export function updateProjectApi(data: ProjectFormData) {
  return request.put('/project/update', data)
}

// 删除项目
export function deleteProjectApi(id: number) {
  return request.delete('/project/delete', { params: { id } })
}

// 提交审核
export function submitProjectApi(id: number) {
  return request.post('/project/submit', { id })
}

// 审核通过
export function approveProjectApi(id: number, remark: string) {
  return request.post('/project/approve', { id, remark })
}

// 审核驳回
export function rejectProjectApi(id: number, remark: string) {
  return request.post('/project/reject', { id, remark })
}

export function batchApproveProjectApi(ids: number[], remark?: string) {
  return request.post('/project/batch-approve', { ids, remark })
}

// 项目列表
export function getProjectListApi(params: { status?: string; category?: string; page?: number; pageSize?: number }) {
  return request.get('/project/list', { params })
}

// 项目详情
export function getProjectDetailApi(id: number) {
  return request.get('/project/detail', { params: { id } })
}

// 我的项目
export function getMyProjectsApi(params: { status?: string; page?: number; pageSize?: number }) {
  return request.get('/project/my', { params })
}
