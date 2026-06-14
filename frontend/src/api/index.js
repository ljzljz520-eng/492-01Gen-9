import request from '@/utils/request'

export const login = (data) => request.post('/api/auth/login', data)
export const getCurrentUser = () => request.get('/api/auth/me')
export const listUsers = (params) => request.get('/api/users', { params })
export const createUser = (data) => request.post('/api/users', data)

export const listStations = () => request.get('/api/stations')
export const getStation = (id) => request.get(`/api/stations/${id}`)
export const createStation = (data) => request.post('/api/stations', data)
export const updateStation = (id, data) => request.put(`/api/stations/${id}`, data)

export const createCharger = (data) => request.post('/api/chargers', data)

export const listGuns = (params) => request.get('/api/guns', { params })
export const updateGunStatus = (id, data) => request.put(`/api/guns/${id}/status`, data)

export const listWorkOrders = (params) => request.get('/api/work-orders', { params })
export const getWorkOrder = (id) => request.get(`/api/work-orders/${id}`)
export const createWorkOrder = (data) => request.post('/api/work-orders', data)
export const updateWorkOrder = (id, data) => request.put(`/api/work-orders/${id}`, data)
export const startWorkOrder = (id) => request.post(`/api/work-orders/${id}/start`)
export const completeWorkOrder = (id) => request.post(`/api/work-orders/${id}/complete`)

export const listRepairRecords = (params) => request.get('/api/repair-records', { params })
export const createRepairRecord = (data) => request.post('/api/repair-records', data)

export const uploadFile = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const getDashboardStats = () => request.get('/api/dashboard/stats')
