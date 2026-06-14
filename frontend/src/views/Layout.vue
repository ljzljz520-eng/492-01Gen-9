<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon :size="28" color="#fff"><Lightning /></el-icon>
        <span>充电桩巡检系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#1f2937"
        text-color="#cbd5e1"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/work-orders">
          <el-icon><Tickets /></el-icon>
          <span>工单管理</span>
        </el-menu-item>
        <el-menu-item v-if="isSupervisorOrAdmin" index="/work-orders/create">
          <el-icon><Plus /></el-icon>
          <span>创建工单</span>
        </el-menu-item>
        <el-menu-item v-if="isSupervisorOrAdmin" index="/stations">
          <el-icon><OfficeBuilding /></el-icon>
          <span>站点管理</span>
        </el-menu-item>
        <el-menu-item v-if="isAdmin" index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-title">{{ currentTitle }}</div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><UserFilled /></el-icon>
              {{ authStore.userName }}
              <span class="role-tag">{{ roleLabel }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => {
  if (route.path.startsWith('/work-orders')) return '/work-orders'
  return route.path
})

const currentTitle = computed(() => route.meta.title || '')

const isSupervisorOrAdmin = computed(() =>
  ['admin', 'supervisor'].includes(authStore.role)
)

const isAdmin = computed(() => authStore.role === 'admin')

const roleLabel = computed(() => {
  const map = {
    admin: '管理员',
    supervisor: '运维主管',
    repairer: '维修员'
  }
  return map[authStore.role] || authStore.role
})

const handleCommand = (cmd) => {
  if (cmd === 'logout') {
    authStore.logout()
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background: #1f2937;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid #374151;
}

:deep(.el-menu) {
  border-right: none;
}

:deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
}

.header {
  background: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 24px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #606266;
  font-size: 14px;
}

.role-tag {
  display: inline-block;
  padding: 2px 8px;
  background: #ecf5ff;
  color: #409EFF;
  border-radius: 4px;
  font-size: 12px;
}

.main-content {
  background: #f5f7fa;
  overflow-y: auto;
}
</style>
