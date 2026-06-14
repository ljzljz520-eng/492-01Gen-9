import { defineStore } from 'pinia'
import { login, getCurrentUser } from '@/api'
import router from '@/router'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    role: (state) => state.user?.role || '',
    userName: (state) => state.user?.full_name || ''
  },
  actions: {
    async doLogin(username, password) {
      const res = await login({ username, password })
      this.token = res.access_token
      localStorage.setItem('token', res.access_token)
      await this.fetchUser()
    },
    async fetchUser() {
      const user = await getCurrentUser()
      this.user = user
      localStorage.setItem('user', JSON.stringify(user))
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      router.push('/login')
    }
  }
})
