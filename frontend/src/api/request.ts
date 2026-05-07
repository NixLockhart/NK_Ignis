import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
})

// 请求拦截器：自动注入 token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器：统一错误处理
request.interceptors.response.use(
  (response) => {
    // blob 响应（文件下载）直接返回，不走 code 检查
    if (response.config.responseType === 'blob') {
      return response
    }
    const res = response.data
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      // 401 未授权，跳转登录
      if (res.code === 401) {
        localStorage.removeItem('token')
        router.push('/login')
      }
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  async (error) => {
    const status = error.response?.status
    let message = ''

    // blob 请求失败时 response.data 是 Blob，需要先解析成 JSON 再取 message
    const raw = error.response?.data
    if (raw instanceof Blob) {
      try {
        const text = await raw.text()
        const json = JSON.parse(text)
        message = json?.message || ''
      } catch {
        // 无法解析时保持空，后续走兜底
      }
    } else if (raw && typeof raw === 'object') {
      message = raw.message || ''
    }

    if (status === 401) {
      // 区分：登录接口返回的401（密码错误）vs Token过期的401
      ElMessage.error(message || '登录已过期，请重新登录')
      // 非登录接口的401才清除token跳转
      if (!error.config?.url?.includes('/auth/login')) {
        localStorage.removeItem('token')
        router.push('/login')
      }
    } else if (status === 403) {
      ElMessage.error(message || '无权限访问')
    } else if (status && status >= 400) {
      ElMessage.error(message || `请求失败 (${status})`)
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请稍后重试')
    } else if (error.code === 'ERR_NETWORK' || !error.response) {
      ElMessage.error(message || '无法连接服务器，请确认后端服务是否运行')
    } else {
      ElMessage.error(message || '网络错误')
    }
    return Promise.reject(error)
  },
)

export default request
