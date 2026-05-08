import request from './request'

export interface LogInfo {
  id: number
  userId: number
  userName: string | null
  action: string
  actionLabel: string
  targetType: string | null
  targetId: number | null
  detail: string | null
  ipAddress: string | null
  createdAt: string | null
}

export interface ActionTypeOption {
  value: string
  label: string
}

export function getLogListApi(params: {
  action?: string
  userId?: number
  startDate?: string
  endDate?: string
  page?: number
  pageSize?: number
}) {
  return request.get('/log/list', { params })
}

export function getActionTypesApi() {
  return request.get('/log/action-types')
}
