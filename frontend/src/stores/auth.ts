import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface User {
  id: string
  email: string
  name?: string
  token: string
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!user.value)
  const userEmail = computed(() => user.value?.email || '')
  const userId = computed(() => user.value?.id || '')

  // Actions
  const login = async (email: string, password: string) => {
    try {
      isLoading.value = true
      error.value = null

      // For demo purposes, accept any email/password combination
      // In production, this would integrate with AWS Cognito
      if (email && password) {
        // Create a consistent user ID based on email
        const userId = `user_${btoa(email).replace(/[^a-zA-Z0-9]/g, '').substring(0, 16)}`
        
        const mockUser: User = {
          id: userId,
          email,
          name: email.split('@')[0],
          token: `mock_token_${Date.now()}`
        }
        
        user.value = mockUser
        localStorage.setItem('noah_user', JSON.stringify(mockUser))
        return mockUser
      } else {
        throw new Error('Email and password are required')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Login failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const logout = () => {
    user.value = null
    localStorage.removeItem('noah_user')
    error.value = null
  }

  const initializeAuth = () => {
    try {
      const savedUser = localStorage.getItem('noah_user')
      if (savedUser) {
        user.value = JSON.parse(savedUser)
      }
    } catch (err) {
      console.error('Failed to initialize auth:', err)
      localStorage.removeItem('noah_user')
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // State
    user,
    isLoading,
    error,
    
    // Getters
    isAuthenticated,
    userEmail,
    userId,
    
    // Actions
    login,
    logout,
    initializeAuth,
    clearError
  }
})