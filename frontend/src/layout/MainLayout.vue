<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import AiFloatWidget from '@/components/AiFloatWidget.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const roleMap: Record<string, string> = { student: '学生', leader: '志愿负责人', admin: '管理员' }
const roleLabel = computed(() => roleMap[userStore.role] || '未知')

// 响应式侧边栏
const collapsed = ref(false)
const isMobile = ref(false)
const drawerVisible = ref(false)

function checkScreen() {
  const w = window.innerWidth
  isMobile.value = w < 768
  collapsed.value = w >= 768 && w < 1024
  if (w >= 768) drawerVisible.value = false
}
onMounted(() => { checkScreen(); window.addEventListener('resize', checkScreen) })
onBeforeUnmount(() => window.removeEventListener('resize', checkScreen))

const sideWidth = computed(() => isMobile.value ? '0px' : collapsed.value ? '64px' : '220px')

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

function menuTitle(item: any): string {
  return resolveDisplayTitle(item.path, item.meta?.title)
}

const topBarTitle = computed(() => {
  // route.path 是绝对路径（如 '/dashboard'），与 menuItems 的 path（'dashboard'）不同
  return resolveDisplayTitle(route.path, route.meta?.title)
})

/**
 * 把"控制台 / dashboard"对学生显示为"首页"，其他情况按 meta.title 显示。
 * 同时被侧栏菜单和顶部标题复用，避免规则散落两处。
 */
function resolveDisplayTitle(path: string | undefined, fallback: unknown): string {
  const normalized = (path || '').replace(/^\//, '')
  if (normalized === 'dashboard' && userStore.role === 'student') return '首页'
  return (fallback as string) || ''
}

function handleLogout() {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<template>
  <el-container class="h-full">
    <!-- 桌面侧边栏 -->
    <el-aside v-if="!isMobile" :width="sideWidth" class="sidebar-aside">
      <div class="sidebar">
        <!-- Logo -->
        <div class="h-14 flex items-center justify-center gap-2 border-b border-white/10 flex-shrink-0">
          <el-icon size="22" color="#7B93FA"><HomeFilled /></el-icon>
          <span v-if="!collapsed" class="text-sm font-bold text-white whitespace-nowrap">志愿服务管理系统</span>
        </div>
        <!-- 菜单 -->
        <nav class="flex-1 overflow-y-auto py-2 px-2">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="'/' + item.path"
            custom
            v-slot="{ isActive, navigate }"
          >
            <div
              class="menu-item"
              :class="{ active: isActive }"
              @click="navigate"
              :title="collapsed ? menuTitle(item) : ''"
            >
              <el-icon size="18"><component :is="item.meta?.icon" /></el-icon>
              <span v-if="!collapsed" class="menu-label">{{ menuTitle(item) }}</span>
            </div>
          </router-link>
        </nav>
      </div>
    </el-aside>

    <!-- 移动端 Drawer 侧边栏 -->
    <el-drawer v-if="isMobile" v-model="drawerVisible" direction="ltr" size="220px" :show-close="false" class="mobile-drawer">
      <template #header>
        <div class="flex items-center gap-2">
          <el-icon size="20" color="#4F6EF7"><HomeFilled /></el-icon>
          <span class="font-bold text-gray-800">志愿服务管理系统</span>
        </div>
      </template>
      <nav class="space-y-1">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="'/' + item.path"
          custom
          v-slot="{ isActive, navigate }"
        >
          <div
            class="flex items-center gap-3 px-4 py-2.5 rounded-lg cursor-pointer text-sm transition"
            :class="isActive ? 'bg-blue-50 text-blue-600 font-semibold' : 'text-gray-600 hover:bg-gray-50'"
            @click="navigate(); drawerVisible = false"
          >
            <el-icon size="18"><component :is="item.meta?.icon" /></el-icon>
            <span>{{ menuTitle(item) }}</span>
          </div>
        </router-link>
      </nav>
    </el-drawer>

    <el-container>
      <!-- 顶部栏 -->
      <el-header class="flex items-center justify-between bg-white shadow-sm" style="height: 52px; padding: 0 20px;">
        <div class="flex items-center gap-3">
          <!-- 移动端汉堡按钮 -->
          <div v-if="isMobile" class="cursor-pointer p-1" @click="drawerVisible = true">
            <el-icon size="22"><Fold /></el-icon>
          </div>
          <span class="text-base font-semibold text-gray-800">{{ topBarTitle }}</span>
        </div>
        <div class="flex items-center gap-3">
          <el-tag :type="userStore.role === 'admin' ? 'danger' : userStore.role === 'leader' ? 'warning' : 'primary'" size="small" round>
            {{ roleLabel }}
          </el-tag>
          <span class="text-sm text-gray-600 hidden sm:inline">{{ userStore.userInfo?.realName || userStore.userInfo?.username }}</span>
          <el-button type="danger" text size="small" @click="handleLogout">退出</el-button>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="bg-[#F7F8FC]">
        <router-view v-slot="{ Component }">
          <transition name="fade-up" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>

    <AiFloatWidget />
  </el-container>
</template>

<style scoped>
.sidebar-aside {
  transition: width 0.3s ease;
  overflow: hidden;
  flex-shrink: 0;
}
.sidebar {
  height: 100%;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  display: flex;
  flex-direction: column;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  margin: 2px 0;
  border-radius: 10px;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
  transition: all 0.2s ease;
  position: relative;
}
.menu-item:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}
.menu-item.active {
  color: #fff;
  background: rgba(79, 110, 247, 0.3);
  font-weight: 600;
}
.menu-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: #4F6EF7;
  border-radius: 0 3px 3px 0;
}
.menu-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
