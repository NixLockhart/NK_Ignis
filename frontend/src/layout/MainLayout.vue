<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import AiFloatWidget from '@/components/AiFloatWidget.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 角色中文映射
const roleMap: Record<string, string> = {
  student: '学生',
  leader: '志愿负责人',
  admin: '管理员',
}

const roleLabel = computed(() => roleMap[userStore.role] || '未知')

// 根据角色过滤菜单
const menuItems = computed(() => {
  const parentRoute = router.getRoutes().find((r) => r.path === '/')
  if (!parentRoute?.children) return []
  return parentRoute.children.filter((child) => {
    if (child.meta?.hidden) return false
    const roles = child.meta?.roles as string[] | undefined
    if (!roles) return true
    return roles.includes(userStore.role)
  })
})

// 菜单标题：学生的"控制台"显示为"首页"
function menuTitle(item: any): string {
  if (item.path === 'dashboard' && userStore.role === 'student') return '首页'
  return (item.meta?.title as string) || ''
}

function handleLogout() {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<template>
  <el-container class="h-full">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="border-r border-gray-200">
      <div class="h-14 flex items-center justify-center border-b border-gray-200">
        <span class="text-base font-bold text-gray-800">志愿服务管理系统</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        class="!border-r-0"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.path"
          :index="'/' + item.path"
        >
          <el-icon>
            <component :is="item.meta?.icon" />
          </el-icon>
          <span>{{ menuTitle(item) }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶部栏 -->
      <el-header class="flex items-center justify-end border-b border-gray-200 bg-white">
        <div class="flex items-center gap-3">
          <el-tag :type="userStore.role === 'admin' ? 'danger' : userStore.role === 'leader' ? 'warning' : 'primary'" size="small">
            {{ roleLabel }}
          </el-tag>
          <span class="text-sm text-gray-600">{{ userStore.userInfo?.realName || userStore.userInfo?.username }}</span>
          <el-button type="danger" text size="small" @click="handleLogout">退出</el-button>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="bg-gray-50">
        <router-view />
      </el-main>
    </el-container>

    <!-- AI 悬浮窗 -->
    <AiFloatWidget />
  </el-container>
</template>
