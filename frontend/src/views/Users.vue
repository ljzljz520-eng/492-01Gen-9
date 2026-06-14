<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-title">用户管理</div>
      <el-button type="primary" @click="showDialog = true; formMode = 'create'">
        <el-icon><Plus /></el-icon>
        新建用户
      </el-button>
    </div>

    <el-card>
      <el-table :data="users" v-loading="loading">
        <el-table-column prop="username" label="用户名" width="160" />
        <el-table-column prop="full_name" label="姓名" width="160" />
        <el-table-column prop="role" label="角色" width="140">
          <template #default="{ row }">
            <el-tag :type="roleTag(row.role)">{{ roleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showDialog" :title="formMode === 'create' ? '新建用户' : '编辑用户'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="formMode === 'edit'" />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="form.full_name" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="formMode === 'create'">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%;">
            <el-option label="管理员" value="admin" />
            <el-option label="运维主管" value="supervisor" />
            <el-option label="维修员" value="repairer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listUsers, createUser } from '@/api'

const loading = ref(false)
const submitting = ref(false)
const users = ref([])
const showDialog = ref(false)
const formMode = ref('create')
const formRef = ref(null)

const form = reactive({
  username: '',
  full_name: '',
  password: '',
  role: 'repairer'
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  full_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const roleLabel = (r) => {
  const map = { admin: '管理员', supervisor: '运维主管', repairer: '维修员' }
  return map[r] || r
}
const roleTag = (r) => {
  const map = { admin: 'danger', supervisor: 'warning', repairer: 'primary' }
  return map[r] || ''
}
const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : '-'

const fetchUsers = async () => {
  loading.value = true
  try {
    users.value = await listUsers()
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        await createUser({ ...form })
        ElMessage.success('创建成功')
        showDialog.value = false
        fetchUsers()
      } finally {
        submitting.value = false
      }
    }
  })
}

onMounted(fetchUsers)
</script>
