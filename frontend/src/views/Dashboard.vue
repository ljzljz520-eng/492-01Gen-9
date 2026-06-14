<template>
  <div>
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <div class="stat-card" style="border-left: 4px solid #409EFF;">
          <div class="stat-label">总工单</div>
          <div class="stat-value" style="color: #409EFF;">{{ stats?.total_orders || 0 }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card" style="border-left: 4px solid #E6A23C;">
          <div class="stat-label">待处理</div>
          <div class="stat-value" style="color: #E6A23C;">{{ stats?.pending_orders || 0 }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card" style="border-left: 4px solid #67C23A;">
          <div class="stat-label">已完成</div>
          <div class="stat-value" style="color: #67C23A;">{{ stats?.completed_orders || 0 }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card" style="border-left: 4px solid #909399;">
          <div class="stat-label">站点数</div>
          <div class="stat-value" style="color: #909399;">{{ stats?.total_stations || 0 }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>枪口状态</span>
            </div>
          </template>
          <div style="display: flex; justify-content: space-around; padding: 20px 0;">
            <div style="text-align: center;">
              <div style="font-size: 36px; color: #67C23A; font-weight: 600;">{{ stats?.online_guns || 0 }}</div>
              <div style="color: #909399; margin-top: 8px;">在线</div>
            </div>
            <div style="text-align: center;">
              <div style="font-size: 36px; color: #F56C6C; font-weight: 600;">{{ stats?.offline_guns || 0 }}</div>
              <div style="color: #909399; margin-top: 8px;">下线</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>工单进度</span>
            </div>
          </template>
          <div style="padding: 10px 0;">
            <div style="margin-bottom: 16px;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span style="color: #606266;">待处理</span>
                <span style="color: #E6A23C;">{{ pendingPercent }}%</span>
              </div>
              <el-progress :percentage="pendingPercent" color="#E6A23C" :stroke-width="14" />
            </div>
            <div style="margin-bottom: 16px;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span style="color: #606266;">进行中</span>
                <span style="color: #409EFF;">{{ inProgressPercent }}%</span>
              </div>
              <el-progress :percentage="inProgressPercent" color="#409EFF" :stroke-width="14" />
            </div>
            <div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span style="color: #606266;">已完成</span>
                <span style="color: #67C23A;">{{ completedPercent }}%</span>
              </div>
              <el-progress :percentage="completedPercent" color="#67C23A" :stroke-width="14" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>最新工单</span>
          <el-button type="primary" size="small" @click="$router.push('/work-orders')">查看全部</el-button>
        </div>
      </template>
      <el-table :data="recentOrders" style="width: 100%">
        <el-table-column prop="order_no" label="工单号" width="180" />
        <el-table-column prop="title" label="工单标题" />
        <el-table-column prop="order_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="orderTypeTag(row.order_type)">{{ orderTypeLabel(row.order_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getDashboardStats, listWorkOrders } from '@/api'

const stats = ref(null)
const recentOrders = ref([])

const pendingPercent = computed(() => {
  if (!stats.value || !stats.value.total_orders) return 0
  return Math.round((stats.value.pending_orders / stats.value.total_orders) * 100)
})

const inProgressPercent = computed(() => {
  if (!stats.value || !stats.value.total_orders) return 0
  return Math.round((stats.value.in_progress_orders / stats.value.total_orders) * 100)
})

const completedPercent = computed(() => {
  if (!stats.value || !stats.value.total_orders) return 0
  return Math.round((stats.value.completed_orders / stats.value.total_orders) * 100)
})

const orderTypeLabel = (t) => {
  const map = {
    gun_fault: '枪口故障',
    offline: '通讯掉线',
    complaint: '用户投诉',
    inspection: '日常巡检'
  }
  return map[t] || t
}

const orderTypeTag = (t) => {
  const map = {
    gun_fault: 'danger',
    offline: 'warning',
    complaint: 'info',
    inspection: 'success'
  }
  return map[t] || ''
}

const statusLabel = (s) => {
  const map = {
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成'
  }
  return map[s] || s
}

const statusTag = (s) => {
  const map = {
    pending: 'warning',
    in_progress: 'primary',
    completed: 'success'
  }
  return map[s] || ''
}

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : '-'

onMounted(async () => {
  stats.value = await getDashboardStats()
  recentOrders.value = (await listWorkOrders())?.slice(0, 5) || []
})
</script>

<style scoped>
.stat-row {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}
</style>
