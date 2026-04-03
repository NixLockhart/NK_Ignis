import request from './request'

export interface CollegeItem {
  id: number
  name: string
  sortOrder: number
}

export function getCollegeListApi() {
  return request.get('/college/list')
}

export function createCollegeApi(data: { name: string; sortOrder?: number }) {
  return request.post('/college', data)
}

export function updateCollegeApi(id: number, data: { name?: string; sortOrder?: number }) {
  return request.put(`/college/${id}`, data)
}

export function deleteCollegeApi(id: number) {
  return request.delete(`/college/${id}`)
}
