<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-title">站点管理</div>
      <el-button type="primary" @click="showStationDialog = true; stationMode = 'create'">
        <el-icon><Plus /></el-icon>
        新建站点
      </el-button>
    </div>

    <el-row :gutter="20">
      <el-col :span="8" v-for="s in stations" :key="s.id">
        <el-card shadow="hover" style="margin-bottom: 20px;">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 600; font-size: 16px;">
                <el-icon color="#409EFF"><OfficeBuilding /></el-icon>
                {{ s.name }}
              </span>
              <el-dropdown>
                <el-button link>
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="editStation(s)">编辑</el-dropdown-item>
                    <el-dropdown-item @click="showChargerDialog = true; currentStation = s">
                      添加充电桩
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
          <div style="color: #606266; line-height: 1.8;">
            <div><el-icon><Location /></el-icon> {{ s.address }}</div>
            <div v-if="s.contact"><el-icon><User /></el-icon> {{ s.contact }}</div>
            <div v-if="s.phone"><el-icon><Phone /></el-icon> {{ s.phone }}</div>
          </div>
          <el-divider style="margin: 12px 0;" />
          <div style="color: #606266; margin-bottom: 8px;">
            <strong>充电桩 ({{ s.chargers?.length || 0 }})</strong>
          </div>
          <div v-for="c in s.chargers" :key="c.id" style="margin-bottom: 12px; padding: 10px; background: #f5f7fa; border-radius: 4px;">
            <div style="font-weight: 500; margin-bottom: 6px;">
              {{ c.serial_number }}
              <span style="color: #909399; font-size: 12px; margin-left: 6px;">{{ c.model }}</span>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
              <el-tag
                v-for="g in c.guns"
                :key="g.id"
                :type="g.status === 'online' ? 'success' : 'danger'"
                effect="light"
                size="small"
                @click="toggleGunStatus(g)"
                style="cursor: pointer;"
              >
                {{ g.gun_number }} · {{ g.status === 'online' ? '在线' : '下线' }}
              </el-tag>
            </div>
          </div>
          <el-empty v-if="!s.chargers?.length" description="暂无充电桩" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showStationDialog" :title="stationMode === 'create' ? '新建站点' : '编辑站点'" width="500px">
      <el-form ref="stationFormRef" :model="stationForm" :rules="stationRules" label-width="100px">
        <el-form-item label="站点名称" prop="name">
          <el-input v-model="stationForm.name" />
        </el-form-item>
        <el-form-item label="站点地址" prop="address">
          <el-input v-model="stationForm.address" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="stationForm.contact" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="stationForm.phone" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showStationDialog = false">取消</el-button>
        <el-button type="primary" :loading="stationSubmitting" @click="submitStation">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showChargerDialog" title="添加充电桩" width="500px">
      <el-form ref="chargerFormRef" :model="chargerForm" :rules="chargerRules" label-width="100px">
        <el-form-item label="所属站点">
          <el-input :model-value="currentStation?.name" disabled />
        </el-form-item>
        <el-form-item label="设备编号" prop="serial_number">
          <el-input v-model="chargerForm.serial_number" placeholder="如: CHA003" />
        </el-form-item>
        <el-form-item label="设备型号">
          <el-input v-model="chargerForm.model" placeholder="如: DC-120KW" />
        </el-form-item>
        <el-form-item label="枪口数量" prop="total_guns">
          <el-input-number v-model="chargerForm.total_guns" :min="1" :max="8" />
        </el-form-item>
        <el-form-item label="枪口编号">
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <el-input
              v-for="(g, idx) in chargerForm.guns"
              :key="idx"
              v-model="g.gun_number"
              placeholder="枪口编号"
              style="width: 150px;"
            />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChargerDialog = false">取消</el-button>
        <el-button type="primary" :loading="chargerSubmitting" @click="submitCharger">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listStations, createStation, updateStation, createCharger, updateGunStatus } from '@/api'

const stations = ref([])
const showStationDialog = ref(false)
const stationMode = ref('create')
const stationFormRef = ref(null)
const stationSubmitting = ref(false)
const editingStationId = ref(null)

const stationForm = reactive({
  name: '',
  address: '',
  contact: '',
  phone: ''
})

const stationRules = {
  name: [{ required: true, message: '请输入站点名称', trigger: 'blur' }],
  address: [{ required: true, message: '请输入站点地址', trigger: 'blur' }]
}

const showChargerDialog = ref(false)
const chargerFormRef = ref(null)
const chargerSubmitting = ref(false)
const currentStation = ref(null)

const chargerForm = reactive({
  station_id: null,
  serial_number: '',
  model: '',
  total_guns: 2,
  guns: [{ gun_number: 'A01' }, { gun_number: 'A02' }]
})

const chargerRules = {
  serial_number: [{ required: true, message: '请输入设备编号', trigger: 'blur' }],
  total_guns: [{ required: true, message: '请输入枪口数量', trigger: 'blur' }]
}

watch(() => chargerForm.total_guns, (newVal) => {
  const current = chargerForm.guns.length
  if (newVal > current) {
    for (let i = current; i < newVal; i++) {
      chargerForm.guns.push({ gun_number: `GUN${String(i + 1).padStart(2, '0')}` })
    }
  } else if (newVal < current) {
    chargerForm.guns.splice(newVal)
  }
})

const fetchStations = async () => {
  stations.value = await listStations()
}

const editStation = (s) => {
  stationMode.value = 'edit'
  editingStationId.value = s.id
  stationForm.name = s.name
  stationForm.address = s.address
  stationForm.contact = s.contact || ''
  stationForm.phone = s.phone || ''
  showStationDialog.value = true
}

const submitStation = async () => {
  if (!stationFormRef.value) return
  await stationFormRef.value.validate(async (valid) => {
    if (valid) {
      stationSubmitting.value = true
      try {
        if (stationMode.value === 'create') {
          await createStation({ ...stationForm })
          ElMessage.success('站点创建成功')
        } else {
          await updateStation(editingStationId.value, { ...stationForm })
          ElMessage.success('站点更新成功')
        }
        showStationDialog.value = false
        fetchStations()
      } finally {
        stationSubmitting.value = false
      }
    }
  })
}

const submitCharger = async () => {
  if (!chargerFormRef.value) return
  await chargerFormRef.value.validate(async (valid) => {
    if (valid) {
      chargerSubmitting.value = true
      try {
        await createCharger({
          station_id: currentStation.value.id,
          serial_number: chargerForm.serial_number,
          model: chargerForm.model,
          total_guns: chargerForm.total_guns,
          guns: chargerForm.guns
        })
        ElMessage.success('充电桩添加成功')
        showChargerDialog.value = false
        chargerForm.serial_number = ''
        chargerForm.model = ''
        chargerForm.total_guns = 2
        chargerForm.guns = [{ gun_number: 'A01' }, { gun_number: 'A02' }]
        fetchStations()
      } finally {
        chargerSubmitting.value = false
      }
    }
  })
}

const toggleGunStatus = async (gun) => {
  const newStatus = gun.status === 'online' ? 'offline' : 'online'
  const action = newStatus === 'offline' ? '下线' : '上线'
  try {
    await ElMessageBox.confirm(`确认将枪口 ${gun.gun_number} ${action}?`, '提示', { type: 'warning' })
    await updateGunStatus(gun.id, { status: newStatus })
    ElMessage.success(`操作成功`)
    fetchStations()
  } catch (e) {
    if (e !== 'cancel') console.error(e)
  }
}

onMounted(fetchStations)
</script>
