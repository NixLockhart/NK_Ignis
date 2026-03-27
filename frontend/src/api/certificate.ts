import request from './request'

export interface CertificateData {
  userName: string
  studentId: string
  college: string
  major: string
  projectTitle: string
  projectCategory: string
  durationHours: number
  startTime: string
  endTime: string
  signInTime: string
  signOutTime: string
}

export interface CertificateItem {
  projectId: number
  projectTitle: string
  durationHours: number
  signInTime: string | null
}

export function getCertificateDataApi(projectId: number) {
  return request.get('/certificate/data', { params: { projectId } })
}

export function getMyCertificateListApi() {
  return request.get('/certificate/my-list')
}
