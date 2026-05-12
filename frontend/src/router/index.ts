import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/login/LoginView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/register/RegisterView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      component: () => import('@/layout/MainLayout.vue'),
      redirect: '/dashboard',
      meta: { requiresAuth: true },
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/DashboardView.vue'),
          meta: { title: '控制台', icon: 'HomeFilled', roles: ['student', 'leader', 'admin'] },
        },
        {
          path: 'project',
          name: 'ProjectList',
          component: () => import('@/views/project/ProjectList.vue'),
          meta: { title: '项目列表', icon: 'List', roles: ['student', 'leader', 'admin'] },
        },
        {
          path: 'project-manage',
          name: 'ProjectManage',
          component: () => import('@/views/project-manage/ProjectManage.vue'),
          meta: { title: '项目管理', icon: 'Setting', roles: ['leader', 'admin'] },
        },
        {
          path: 'project-review',
          name: 'ProjectReview',
          component: () => import('@/views/project-manage/ProjectReview.vue'),
          meta: { title: '项目审核', icon: 'Checked', roles: ['admin'] },
        },
        {
          path: 'project/:id',
          name: 'ProjectDetail',
          component: () => import('@/views/project/ProjectDetail.vue'),
          meta: { title: '项目详情', roles: ['student', 'leader', 'admin'], hidden: true },
        },
        {
          path: 'my-applications',
          name: 'MyApplications',
          component: () => import('@/views/application/MyApplications.vue'),
          meta: { title: '我的报名', icon: 'Tickets', roles: ['student'] },
        },
        {
          path: 'application-manage',
          name: 'ApplicationManage',
          component: () => import('@/views/application/ApplicationManage.vue'),
          meta: { title: '报名管理', icon: 'UserFilled', roles: ['leader', 'admin'] },
        },
        {
          path: 'my-checkins',
          name: 'MyCheckins',
          component: () => import('@/views/checkin/MyCheckins.vue'),
          meta: { title: '我的打卡', icon: 'Clock', roles: ['student'] },
        },
        {
          path: 'checkin-manage',
          name: 'CheckinManage',
          component: () => import('@/views/checkin/CheckinManage.vue'),
          meta: { title: '打卡管理', icon: 'Timer', roles: ['leader', 'admin'] },
        },
        {
          path: 'my-profile',
          name: 'MyProfile',
          component: () => import('@/views/profile/MyProfile.vue'),
          meta: { title: '个人档案', icon: 'User', roles: ['student'] },
        },
        {
          path: 'certificate/:projectId',
          name: 'CertificatePreview',
          component: () => import('@/views/certificate/CertificatePreview.vue'),
          meta: { title: '证书预览', roles: ['student'], hidden: true },
        },
        {
          path: 'operation-log',
          name: 'OperationLog',
          component: () => import('@/views/admin/OperationLog.vue'),
          meta: { title: '操作日志', icon: 'Document', roles: ['admin'] },
        },
        {
          path: 'user-manage',
          name: 'UserManage',
          component: () => import('@/views/admin/UserManage.vue'),
          meta: { title: '用户管理', icon: 'UserFilled', roles: ['admin'] },
        },
        {
          path: 'college-manage',
          name: 'CollegeManage',
          component: () => import('@/views/admin/CollegeManage.vue'),
          meta: { title: '学院管理', icon: 'School', roles: ['admin'] },
        },
        {
          path: 'statistics',
          name: 'Statistics',
          component: () => import('@/views/statistics/StatisticsView.vue'),
          meta: { title: '统计报表', icon: 'DataAnalysis', roles: ['admin'] },
        },
      ],
    },
    // 404 兜底
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/error/NotFound.vue'),
      meta: { requiresAuth: false },
    },
  ],
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  const userStore = useUserStore()

  // 不需要登录的页面直接放行
  if (to.meta.requiresAuth === false) {
    // 已登录时不允许访问登录/注册页
    if (userStore.isLoggedIn && (to.name === 'Login' || to.name === 'Register')) {
      return next('/dashboard')
    }
    return next()
  }

  // 需要登录但未登录，跳转登录页
  if (!userStore.isLoggedIn) {
    return next('/login')
  }

  // 已登录但未获取用户信息，尝试获取
  if (!userStore.userInfo) {
    try {
      await userStore.fetchProfile()
    } catch {
      userStore.logout()
      return next('/login')
    }
  }

  // 角色权限校验
  const roles = to.meta.roles as string[] | undefined
  if (roles && roles.length > 0 && !roles.includes(userStore.role)) {
    return next('/dashboard')
  }

  next()
})

export default router
