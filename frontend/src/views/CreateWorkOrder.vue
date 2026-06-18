<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-title">
        <el-button link @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <span style="margin-left: 8px;">创建工单</span>
      </div>
    </div>

    <el-card style="max-width: 900px;">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="工单类型" prop="order_type">
          <el-radio-group v-model="form.order_type">
            <el-radio label="gun_fault">枪口故障</el-radio>
            <el-radio label="offline">通讯掉线</el-radio>
            <el-radio label="complaint">用户投诉</el-radio>
            <el-radio label="inspection">日常巡检</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="工单标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入工单标题" maxlength="200" show-word-limit />
        </el-form-item>

        <el-form-item label="优先级" prop="priority">
          <el-radio-group v-model="form.priority">
            <el-radio label="low">低</el-radio>
            <el-radio label="normal">中</el-radio>
            <el-radio label="high">高</el-radio>
            <el-radio label="urgent">紧急</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="选择站点" :required="needStation">
          <el-select
            v-model="selectedStationId"
            placeholder="请选择站点"
            filterable
            clearable
            style="width: 300px;"
            @change="handleStationChange"
          >
            <el-option
              v-for="s in stations"
              :key="s.id"
              :label="s.name"
              :value="s.id"
            />
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            {{ stationTip }}
          </div>
        </el-form-item>

        <el-form-item label="关联枪口" :required="needGun">
          <el-select
            v-model="form.gun_id"
            placeholder="请选择关联的枪口"
            filterable
            clearable
            style="width: 300px;"
            :disabled="!selectedStationId"
          >
            <el-option
              v-for="g in availableGuns"
              :key="g.id"
              :label="`${g.charger_serial || ''} - ${g.gun_number} (${g.status === 'online' ? '在线' : '下线'})`"
              :value="g.id"
            />
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            {{ gunTip }}
          </div>
        </el-form-item>

        <el-form-item label="派单给">
          <el-select
            v-model="form.assignee_id"
            placeholder="请选择维修员"
            filterable
            clearable
            style="width: 300px;"
          >
            <el-option
              v-for="u in repairers"
              :key="u.id"
              :label="u.full_name"
              :value="u.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="下线枪口" v-if="form.gun_id">
          <el-switch
            v-model="form.take_gun_offline"
            active-text="严重故障需临时下线"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            开启后，对应枪口将被设置为下线状态，工单完成后自动恢复
          </div>
        </el-form-item>

        <el-form-item label="工单描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="5"
            placeholder="请详细描述故障情况或巡检要求"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">提交工单</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createWorkOrder, listStations, listGuns, listUsers } from '@/api'

const router = useRouter()
const formRef = ref(null)
const submitting = ref(false)
const stations = ref([])
const allGuns = ref([])
const repairers = ref([])
const selectedStationId = ref(null)

const form = reactive({
  order_type: 'gun_fault',
  title: '',
  priority: 'normal',
  description: '',
  gun_id: null,
  assignee_id: null,
  take_gun_offline: false
})

const rules = {
  order_type: [{ required: true, message: '请选择工单类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入工单标题', trigger: 'blur' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
  description: [{ required: true, message: '请输入工单描述', trigger: 'blur' }]
}

const needStation = computed(() => form.order_type === 'gun_fault')
const needGun = computed(() => form.order_type === 'gun_fault')

const stationTip = computed(() => {
  const tips = {
    gun_fault: '枪口故障必须选择站点',
    offline: '可选：如需定位具体充电桩请选择站点',
    complaint: '可选：用户投诉可不选站点',
    inspection: '建议选择巡检站点'
  }
  return tips[form.order_type] || ''
})

const gunTip = computed(() => {
  const tips = {
    gun_fault: '枪口故障必须选择具体枪口',
    offline: '可选：已知具体枪口可直接选择',
    complaint: '可选：已知具体枪口可直接选择',
    inspection: '可选：巡检特定枪口可选择'
  }
  return tips[form.order_type] || ''
})

const availableGuns = computed(() => {
  if (!selectedStationId.value) return []
  return allGuns.value.filter(g => g.station_id === selectedStationId.value)
})

const handleStationChange = () => {
  form.gun_id = null
}

const fetchData = async () => {
  const [sList, gList, uList] = await Promise.all([
    listStations(),
    listGuns(),
    listUsers({ role: 'repairer' })
  ])
  stations.value = sList
  repairers.value = uList

  const gunMap = {}
  sList.forEach(s => {
    s.chargers.forEach(c => {
      c.guns.forEach(g => {
        gunMap[g.id] = {
          ...g,
          station_id: s.id,
          charger_serial: c.serial_number
        }
      })
    })
  })
  allGuns.value = Object.values(gunMap).length ? Object.values(gunMap) : gList
}

const handleSubmit = async () => {
  if (!formRef.value) return

  if (form.order_type === 'gun_fault') {
    if (!selectedStationId.value) {
      ElMessage.warning('枪口故障必须选择站点')
      return
    }
    if (!form.gun_id) {
      ElMessage.warning('枪口故障必须选择具体枪口')
      return
    }
  }

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const result = await createWorkOrder(form)
        ElMessage.success('工单创建成功')
        router.push(`/work-orders/${result.id}`)
      } finally {
        submitting.value = false
      }
    }
  })
}

onMounted(fetchData)
</script>
