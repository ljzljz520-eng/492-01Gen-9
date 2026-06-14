<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-title">
        <el-button link @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <span style="margin-left: 8px;">工单详情 - {{ order?.order_no }}</span>
      </div>
      <div>
        <el-button
          v-if="order?.status === 'pending' && (isSupervisorOrAdmin || (isRepairer && !order.assignee_id))"
          type="success"
          @click="handleStart"
        >开始处理</el-button>
        <el-button
          v-if="order?.status === 'in_progress' && canComplete"
          type="primary"
          @click="handleComplete"
        >完成工单</el-button>
      </div>
    </div>

    <el-descriptions :column="2" border size="default" v-if="order">
      <el-descriptions-item label="工单号">{{ order.order_no }}</el-descriptions-item>
      <el-descriptions-item label="工单类型">
        <el-tag :type="orderTypeTag(order.order_type)">{{ orderTypeLabel(order.order_type) }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="工单标题">{{ order.title }}</el-descriptions-item>
      <el-descriptions-item label="优先级">
        <el-tag :type="priorityTag(order.priority)">{{ priorityLabel(order.priority) }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="statusTag(order.status)">{{ statusLabel(order.status) }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="关联枪口">
        <span v-if="order.gun">
          {{ order.gun.gun_number }}
          <el-tag :type="order.gun.status === 'online' ? 'success' : 'danger'" size="small" style="margin-left: 8px;">
            {{ order.gun.status === 'online' ? '在线' : '下线' }}
          </el-tag>
        </span>
        <span v-else>-</span>
      </el-descriptions-item>
      <el-descriptions-item label="派单人">{{ order.creator?.full_name || '-' }}</el-descriptions-item>
      <el-descriptions-item label="维修员">{{ order.assignee?.full_name || '-' }}</el-descriptions-item>
      <el-descriptions-item label="是否下线枪口">
        <el-tag :type="order.take_gun_offline ? 'danger' : 'info'">
          {{ order.take_gun_offline ? '是' : '否' }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ formatDate(order.created_at) }}</el-descriptions-item>
      <el-descriptions-item label="工单描述" :span="2">
        {{ order.description || '-' }}
      </el-descriptions-item>
    </el-descriptions>

    <el-card style="margin-top: 20px;">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: 600;">维修记录</span>
          <el-button
            v-if="order?.status === 'in_progress' && canAddRecord"
            type="primary"
            size="small"
            @click="showRecordDialog = true"
          >
            <el-icon><Plus /></el-icon>
            添加记录
          </el-button>
        </div>
      </template>
      <el-timeline v-if="records.length">
        <el-timeline-item
          v-for="r in records"
          :key="r.id"
          :timestamp="formatDate(r.created_at)"
          placement="top"
        >
          <el-card shadow="never" style="margin-bottom: 10px;">
            <div style="margin-bottom: 8px;">
              <strong>{{ r.repairer?.full_name }}</strong>
              <span style="color: #909399; margin-left: 12px;">到站时间: {{ formatDate(r.arrive_time) }}</span>
            </div>
            <el-descriptions :column="3" size="small" border>
              <el-descriptions-item label="电压测量">
                {{ r.voltage_measurement != null ? r.voltage_measurement + ' V' : '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="是否换件">
                <el-tag :type="r.parts_replaced ? 'warning' : 'info'" size="small">
                  {{ r.parts_replaced ? '是' : '否' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="换件说明">{{ r.parts_description || '-' }}</el-descriptions-item>
              <el-descriptions-item label="维修说明" :span="3">
                {{ r.repair_description || '-' }}
              </el-descriptions-item>
            </el-descriptions>
            <div v-if="r.photo_urls" style="margin-top: 12px;">
              <div style="color: #606266; margin-bottom: 6px;">现场照片:</div>
              <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <img
                  v-for="(url, idx) in parsePhotos(r.photo_urls)"
                  :key="idx"
                  :src="url"
                  style="width: 120px; height: 120px; object-fit: cover; border-radius: 4px; cursor: pointer;"
                  @click="previewImage(url)"
                />
              </div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="暂无维修记录" />
    </el-card>

    <el-dialog v-model="showRecordDialog" title="添加维修记录" width="600px">
      <el-form ref="recordFormRef" :model="recordForm" :rules="recordRules" label-width="100px">
        <el-form-item label="电压测量" prop="voltage_measurement">
          <el-input-number v-model="recordForm.voltage_measurement" :min="0" :max="1000" :step="0.1" style="width: 200px;" />
          <span style="margin-left: 8px; color: #909399;">V</span>
        </el-form-item>
        <el-form-item label="是否换件">
          <el-switch v-model="recordForm.parts_replaced" />
        </el-form-item>
        <el-form-item label="换件说明" v-if="recordForm.parts_replaced">
          <el-input v-model="recordForm.parts_description" type="textarea" :rows="2" placeholder="请描述更换的零部件" />
        </el-form-item>
        <el-form-item label="维修说明" prop="repair_description">
          <el-input v-model="recordForm.repair_description" type="textarea" :rows="3" placeholder="请描述维修过程" />
        </el-form-item>
        <el-form-item label="现场照片">
          <el-upload
            :action="uploadAction"
            :headers="uploadHeaders"
            list-type="picture-card"
            :on-success="handleUploadSuccess"
            :before-remove="handleBeforeRemove"
            :file-list="fileList"
            multiple
            accept="image/*"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRecordDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitRecord">提交</el-button>
      </template>
    </el-dialog>

    <el-image-viewer
      v-if="showViewer"
      :url-list="[viewerUrl]"
      @close="showViewer = false"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getWorkOrder, listRepairRecords, startWorkOrder, completeWorkOrder,
  createRepairRecord, uploadFile
} from '@/api'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()
const order = ref(null)
const records = ref([])
const showRecordDialog = ref(false)
const submitting = ref(false)
const recordFormRef = ref(null)
const fileList = ref([])
const uploadedUrls = ref([])
const showViewer = ref(false)
const viewerUrl = ref('')

const uploadAction = '/api/upload'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

const isSupervisorOrAdmin = computed(() => ['admin', 'supervisor'].includes(authStore.role))
const isRepairer = computed(() => authStore.role === 'repairer')
const currentUserId = computed(() => authStore.user?.id)
const canComplete = computed(() => {
  if (isSupervisorOrAdmin.value) return true
  return isRepairer.value && order.value?.assignee_id === currentUserId.value
})
const canAddRecord = computed(() => {
  if (isSupervisorOrAdmin.value) return true
  return isRepairer.value && order.value?.assignee_id === currentUserId.value
})

const recordForm = reactive({
  voltage_measurement: null,
  parts_replaced: false,
  parts_description: '',
  repair_description: ''
})

const recordRules = {
  repair_description: [{ required: true, message: '请输入维修说明', trigger: 'blur' }]
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
const parsePhotos = (urls) => urls ? urls.split(',').filter(Boolean) : []

const fetchData = async () => {
  const id = route.params.id
  order.value = await getWorkOrder(id)
  records.value = await listRepairRecords({ work_order_id: id })
}

const handleStart = async () => {
  try {
    await ElMessageBox.confirm('确认开始处理此工单?', '提示', { type: 'warning' })
    await startWorkOrder(order.value.id)
    ElMessage.success('工单已开始')
    fetchData()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

const handleComplete = async () => {
  try {
    await ElMessageBox.confirm('确认完成此工单？完成后关联枪口将自动恢复上线。', '提示', { type: 'warning' })
    await completeWorkOrder(order.value.id)
    ElMessage.success('工单已完成，枪口已恢复上线')
    fetchData()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

const handleUploadSuccess = (response, uploadFile) => {
  uploadedUrls.value.push(response.url)
  fileList.value.push({ name: uploadFile.name, url: response.url })
}

const handleBeforeRemove = (file) => {
  const idx = uploadedUrls.value.indexOf(file.url)
  if (idx > -1) uploadedUrls.value.splice(idx, 1)
  return true
}

const submitRecord = async () => {
  if (!recordFormRef.value) return
  await recordFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        await createRepairRecord({
          work_order_id: order.value.id,
          ...recordForm,
          photo_urls: uploadedUrls.value.join(',')
        })
        ElMessage.success('记录已添加')
        showRecordDialog.value = false
        fileList.value = []
        uploadedUrls.value = []
        recordForm.voltage_measurement = null
        recordForm.parts_replaced = false
        recordForm.parts_description = ''
        recordForm.repair_description = ''
        fetchData()
      } finally {
        submitting.value = false
      }
    }
  })
}

const previewImage = (url) => {
  viewerUrl.value = url
  showViewer.value = true
}

onMounted(fetchData)
</script>
