import request from './request'

export interface EvaluationInfo {
  id: number
  projectId: number
  projectTitle: string | null
  userId: number
  userName: string | null
  evaluatorRole: string
  targetUserId: number | null
  targetUserName: string | null
  score: number
  content: string
  createdAt: string | null
}

// 学生评价活动
export function createEvaluationApi(projectId: number, score: number, content: string) {
  return request.post('/evaluation/create', { projectId, score, content })
}

// 负责人评价学生
export function createLeaderCommentApi(projectId: number, targetUserId: number, score: number, content: string) {
  return request.post('/evaluation/leader-comment', { projectId, targetUserId, score, content })
}

// 某项目评价列表
export function getEvaluationListApi(params: { projectId: number; page?: number; pageSize?: number }) {
  return request.get('/evaluation/list', { params })
}

// 我的评价记录
export function getMyEvaluationsApi(params: { page?: number; pageSize?: number }) {
  return request.get('/evaluation/my', { params })
}
