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

export interface CertTemplate {
  id: number
  name: string
  bgColor: string
  accentColor: string
  signatureText: string
  commendationStyle: string
  commendationStyleLabel: string
  isDefault: boolean
  enabled: boolean
  createdAt: string
  updatedAt: string
}

export interface EligibleStudent {
  id: number
  realName: string
  studentId: string
  college: string
}

export function getCertificateDataApi(projectId: number) {
  return request.get('/certificate/data', { params: { projectId } })
}

export function getMyCertificateListApi() {
  return request.get('/certificate/my-list')
}

// ========== 证书 PDF 下载 ==========

export function downloadCertificatePdfApi(projectId: number, templateId?: number, userId?: number) {
  return request.get('/certificate/pdf', {
    params: { projectId, templateId, userId },
    responseType: 'blob',
  }).then((res) => {
    const disposition = res.headers['content-disposition'] || ''
    const match = disposition.match(/filename\*?=(?:UTF-8'')?([^;]+)/i)
    const fileName = match ? decodeURIComponent(match[1].replace(/"/g, '')) : 'certificate.pdf'
    triggerDownload(res.data, fileName)
  })
}

export function downloadBatchCertificateZipApi(projectId: number, templateId?: number) {
  return request.post('/certificate/batch-pdf', { projectId, templateId }, {
    responseType: 'blob',
  }).then((res) => {
    const disposition = res.headers['content-disposition'] || ''
    const match = disposition.match(/filename\*?=(?:UTF-8'')?([^;]+)/i)
    const fileName = match ? decodeURIComponent(match[1].replace(/"/g, '')) : 'certificates.zip'
    triggerDownload(res.data, fileName)
  })
}

// ========== 证书模板管理 ==========

export function getCertTemplatesApi(onlyEnabled = true) {
  return request.get('/certificate/templates', { params: { enabled: onlyEnabled } })
}

export function createCertTemplateApi(payload: Partial<CertTemplate>) {
  return request.post('/certificate/template', payload)
}

export function updateCertTemplateApi(id: number, payload: Partial<CertTemplate>) {
  return request.put(`/certificate/template/${id}`, payload)
}

export function deleteCertTemplateApi(id: number) {
  return request.delete(`/certificate/template/${id}`)
}

export function getEligibleStudentsApi(projectId: number) {
  return request.get('/certificate/eligible-users', { params: { projectId } })
}

// ========== 工具函数 ==========

function triggerDownload(blob: Blob, fileName: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
