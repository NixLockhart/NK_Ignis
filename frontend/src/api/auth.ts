import request from './request'

export interface LoginParams {
  username: string
  password: string
}

export interface RegisterParams {
  username: string
  password: string
  realName: string
  studentId: string
  college: string
  major: string
  phone: string
}

export interface UserInfo {
  id: number
  username: string
  realName: string
  studentId: string
  college: string
  major: string
  role: string
  phone: string
}

// 登录
export function loginApi(data: LoginParams) {
  return request.post('/auth/login', data)
}

// 注册
export function registerApi(data: RegisterParams) {
  return request.post('/auth/register', data)
}

// 获取当前用户信息
export function getProfileApi() {
  return request.get('/auth/profile')
}

// 更新个人信息
export interface UpdateProfileParams {
  realName?: string
  college?: string
  major?: string
  phone?: string
}

export function updateProfileApi(data: UpdateProfileParams) {
  return request.put('/auth/profile', data)
}

// 管理员：获取用户列表
export function getUserListApi(params: { page?: number; pageSize?: number; role?: string; keyword?: string }) {
  return request.get('/auth/users', { params })
}

// 管理员：修改用户角色
export function changeRoleApi(userId: number, role: string) {
  return request.put('/auth/role', { userId, role })
}

// 用户：自助修改密码
export function changePasswordApi(oldPassword: string, newPassword: string) {
  return request.post('/auth/change-password', { oldPassword, newPassword })
}

// 管理员：重置用户密码（不传 newPassword 时后端默认重置为 123456）
export function resetPasswordApi(userId: number, newPassword?: string) {
  return request.post('/auth/reset-password', { userId, newPassword })
}
