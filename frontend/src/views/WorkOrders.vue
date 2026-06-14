<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-title">工单管理</div>
      <el-button
        v-if="isSupervisorOrAdmin"
        type="primary"
        @click="$router.push('/work-orders/create')"
      >
        <el-icon><Plus /></el-icon>
        创建工单
      </el-button>
    </div>

    <div class="filter-bar">
      <el-select v-model="filters.status" placeholder="工单状态" clearable style="width: 140px;">
        <el-option label="待处理" value="pending" />
        <el-option label="进行中" value="in_progress" />
        <el-option label="已完成" value="completed" />
      </el-select>
      <el-select v-model="filters.order_type" placeholder="工单类型" clearable style="width: 140px;">
        <el-option label="枪口故障" value="gun_fault" />
        <el-option label="通讯掉线" value="offline" />
        <el-option label="用户投诉" value="complaint" />
        <el-option label="日常巡检" value="inspection" />
      </el-select>
      <el-button type="primary" @click="fetchOrders">查询</el-button>
      <el-button @click="resetFilters">重置</el-button>
    </div>

    <el-card>
      <el-table :data="orders" v-loading="loading">
        <el-table-column prop="order_no" label="工单号" width="180" />
        <el-table-column prop="title" label="工单标题" />
        <el-table-column prop="order_type" label="类型" width="110">
          <template #default="{ row }">
            <el-tag :type="orderTypeTag(row.order_type)">{{ orderTypeLabel(row.order_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="90">
          <template #default="{ row }">
            <el-tag :type="priorityTag(row.priority)">{{ priorityLabel(row.priority) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="派单人" width="100">
          <template #default="{ row }">{{ row.creator?.full_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="维修员" width="100">
          <template #default="{ row }">{{ row.assignee?.full_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewDetail(row)">查看</el-button>
            <el-button
              v-if="(row.status === 'pending') && (isSupervisorOrAdmin || (isRepairer && !row.assignee_id))"
              type="success"
              size="small"
              @click="handleStart(row)"
            >开始</el-button>
            <el-button
              v-if="row.status === 'in_progress' && (isSupervisorOrAdmin || (isRepairer && row.assignee_id === currentUserId))"
              type="warning"
              size="small"
              @click="viewDetail(row)"
            >处理</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listWorkOrders, startWorkOrder } from '@/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const orders = ref([])

const filters = reactive({
  status: '',
  order_type: ''
})

const isSupervisorOrAdmin = computed(() => ['admin', 'supervisor'].includes(authStore.role))
const isRepairer = computed(() => authStore.role === 'repairer')
const currentUserId = computed(() => authStore.user?.id)

const fetchOrders = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.status) params.status = filters.status
    if (filters.order_type) params.order_type = filters.order_type
    orders.value = await listWorkOrders(params)
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.status = ''
  filters.order_type = ''
  fetchOrders()
}

const orderTypeLabel = (t) => {
  const map = { gun_fault: '枪口故障', offline: '通讯掉线', complaint: '用户投诉', inspection: '日常巡检' }
  return map[t] || t
}
const orderTypeTag = (t) => {
  const map = { gun_fault: 'danger', offline: 'warning', complaint: 'info', inspection: 'success' }
  return map[t] || ''
}
const priorityLabel = (p) => {
  const map = { low: '低', normal: '中', high: '高', urgent: '紧急' }
  return map[p] || p
}
const priorityTag = (p) => {
  const map = { low: 'info', normal: '', high: 'warning', urgent: 'danger' }
  return map[p] || ''
}
const statusLabel = (s) => {
  const map = { pending: '待处理', in_progress: '进行中', completed: '已完成' }
  return map[s] || s
}
const statusTag = (s) => {
  const map = { pending: 'warning', in_progress: 'primary', completed: 'success' }
  return map[s] || ''
}
const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : '-'

const viewDetail = (row) => {
  router.push(`/work-orders/${row.id}`)
}

const handleStart = async (row) => {
  try {
    await ElMessageBox.confirm(`确认开始处理工单 ${row.order_no}?`, '提示', { type: 'warning' })
    await startWorkOrder(row.id)
    ElMessage.success('工单已开始')
    fetchOrders()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

onMounted(fetchOrders)
</script>
