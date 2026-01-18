import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, ChatSession } from '@/types/chat'
import { useAuthStore } from '@/stores/auth'

export const useChatStore = defineStore('chat', () => {
  // State
  const currentSession = ref<ChatSession | null>(null)
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const sortedMessages = computed(() => {
    return [...messages.value].sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )
  })

  const hasMessages = computed(() => messages.value.length > 0)

  // Actions
  const initializeSession = (userId?: string) => {
    const authStore = useAuthStore()
    const actualUserId = userId || authStore.userId
    
    if (!actualUserId) {
      throw new Error('User ID is required to initialize session')
    }

    const sessionId = `session_${actualUserId}_${Date.now()}`
    currentSession.value = {
      sessionId,
      userId: actualUserId,
      messages: [],
      isActive: true,
      lastActivity: new Date()
    }
    
    // Load existing messages for this user
    loadUserMessages(actualUserId)
    error.value = null
  }

  const loadUserMessages = (userId: string) => {
    try {
      // Load messages from localStorage for this specific user
      const storageKey = `noah_messages_${userId}`
      const savedMessages = localStorage.getItem(storageKey)
      
      if (savedMessages) {
        const parsedMessages = JSON.parse(savedMessages)
        messages.value = parsedMessages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }))
      } else {
        messages.value = []
      }
    } catch (err) {
      console.error('Failed to load user messages:', err)
      messages.value = []
    }
  }

  const saveUserMessages = (userId: string) => {
    try {
      const storageKey = `noah_messages_${userId}`
      localStorage.setItem(storageKey, JSON.stringify(messages.value))
    } catch (err) {
      console.error('Failed to save user messages:', err)
    }
  }

  const addMessage = (message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const authStore = useAuthStore()
    
    const newMessage: ChatMessage = {
      ...message,
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    }
    
    messages.value.push(newMessage)
    
    if (currentSession.value) {
      currentSession.value.lastActivity = new Date()
      currentSession.value.messages.push(newMessage)
    }
    
    // Save messages for the current user
    if (authStore.userId) {
      saveUserMessages(authStore.userId)
    }
    
    return newMessage
  }

  const addUserMessage = (content: string) => {
    return addMessage({
      content,
      sender: 'user',
      type: 'text'
    })
  }

  const addNoahMessage = (content: string, type: ChatMessage['type'] = 'text', metadata?: ChatMessage['metadata']) => {
    return addMessage({
      content,
      sender: 'noah',
      type,
      metadata
    })
  }

  const addStreamingMessage = (content: string, type: ChatMessage['type'] = 'text') => {
    const authStore = useAuthStore()
    
    const newMessage: ChatMessage = {
      id: `msg_streaming_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      content,
      sender: 'noah',
      type,
      timestamp: new Date()
    }
    
    messages.value.push(newMessage)
    
    if (currentSession.value) {
      currentSession.value.lastActivity = new Date()
      currentSession.value.messages.push(newMessage)
    }
    
    // Save messages for the current user
    if (authStore.userId) {
      saveUserMessages(authStore.userId)
    }
    
    return newMessage
  }

  const updateStreamingMessage = (messageId: string, content: string, metadata?: ChatMessage['metadata'], append: boolean = false) => {
    const authStore = useAuthStore()
    const messageIndex = messages.value.findIndex(msg => msg.id === messageId)
    
    if (messageIndex !== -1) {
      if (append) {
        // Append new content to existing content
        messages.value[messageIndex].content += content
      } else {
        // Replace content (for backward compatibility)
        messages.value[messageIndex].content = content
      }
      
      if (metadata) {
        messages.value[messageIndex].metadata = metadata
      }
      
      // Update in session as well
      if (currentSession.value) {
        const sessionMessageIndex = currentSession.value.messages.findIndex(msg => msg.id === messageId)
        if (sessionMessageIndex !== -1) {
          if (append) {
            currentSession.value.messages[sessionMessageIndex].content += content
          } else {
            currentSession.value.messages[sessionMessageIndex].content = content
          }
          if (metadata) {
            currentSession.value.messages[sessionMessageIndex].metadata = metadata
          }
        }
      }
      
      // Save updated messages for the current user
      if (authStore.userId) {
        saveUserMessages(authStore.userId)
      }
    }
  }

  const appendToStreamingMessage = (messageId: string, content: string, metadata?: ChatMessage['metadata']) => {
    updateStreamingMessage(messageId, content, metadata, true)
  }

  const finalizeStreamingMessage = (messageId: string, finalContent?: string, metadata?: ChatMessage['metadata']) => {
    // If finalContent is provided, replace the entire content (for cases where backend sends complete message)
    // Otherwise, just mark as finalized (content was already accumulated via chunks)
    if (finalContent) {
      updateStreamingMessage(messageId, finalContent, metadata, false)
    } else if (metadata) {
      updateStreamingMessage(messageId, '', metadata, false)
    }
  }

  const clearMessages = () => {
    const authStore = useAuthStore()
    messages.value = []
    
    if (currentSession.value) {
      currentSession.value.messages = []
    }
    
    // Clear saved messages for the current user
    if (authStore.userId) {
      const storageKey = `noah_messages_${authStore.userId}`
      localStorage.removeItem(storageKey)
    }
  }

  const clearAllUserData = () => {
    // Clear current session data
    messages.value = []
    currentSession.value = null
    error.value = null
  }

  const setLoading = (loading: boolean) => {
    isLoading.value = loading
  }

  const setError = (errorMessage: string | null) => {
    error.value = errorMessage
  }

  const loadMessageHistory = async (sessionId: string) => {
    try {
      setLoading(true)
      setError(null)
      
      // TODO: Implement API call to load message history from backend
      // For now, messages are loaded from localStorage in loadUserMessages
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load message history')
    } finally {
      setLoading(false)
    }
  }

  return {
    // State
    currentSession,
    messages,
    isLoading,
    error,
    
    // Getters
    sortedMessages,
    hasMessages,
    
    // Actions
    initializeSession,
    loadUserMessages,
    addMessage,
    addUserMessage,
    addNoahMessage,
    addStreamingMessage,
    updateStreamingMessage,
    appendToStreamingMessage,
    finalizeStreamingMessage,
    clearMessages,
    clearAllUserData,
    setLoading,
    setError,
    loadMessageHistory
  }
})