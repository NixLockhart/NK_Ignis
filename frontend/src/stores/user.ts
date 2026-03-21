import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, getProfileApi, type LoginParams, type UserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const role = computed(() => userInfo.value?.role || '')

  // 登录
  async function login(params: LoginParams) {
    const res = await loginApi(params)
    token.value = res.data.token
    localStorage.setItem('token', res.data.token)
    await fetchProfile()
  }

  // 获取用户信息
  async function fetchProfile() {
    const res = await getProfileApi()
    userInfo.value = res.data
  }

  // 退出登录
  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  return { token, userInfo, isLoggedIn, role, login, fetchProfile, logout }
})
