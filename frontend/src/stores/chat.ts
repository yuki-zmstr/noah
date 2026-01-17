import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, ChatSession } from '@/types/chat'

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
  const initializeSession = (userId: string) => {
    const sessionId = `session_${userId}_${Date.now()}`
    currentSession.value = {
      sessionId,
      userId,
      messages: [],
      isActive: true,
      lastActivity: new Date()
    }
    messages.value = []
    error.value = null
  }

  const addMessage = (message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
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
    
    return newMessage
  }

  const updateStreamingMessage = (messageId: string, content: string, metadata?: ChatMessage['metadata']) => {
    const messageIndex = messages.value.findIndex(msg => msg.id === messageId)
    if (messageIndex !== -1) {
      messages.value[messageIndex].content = content
      if (metadata) {
        messages.value[messageIndex].metadata = metadata
      }
      
      // Update in session as well
      if (currentSession.value) {
        const sessionMessageIndex = currentSession.value.messages.findIndex(msg => msg.id === messageId)
        if (sessionMessageIndex !== -1) {
          currentSession.value.messages[sessionMessageIndex].content = content
          if (metadata) {
            currentSession.value.messages[sessionMessageIndex].metadata = metadata
          }
        }
      }
    }
  }

  const finalizeStreamingMessage = (messageId: string, finalContent: string, metadata?: ChatMessage['metadata']) => {
    updateStreamingMessage(messageId, finalContent, metadata)
  }

  const clearMessages = () => {
    messages.value = []
    if (currentSession.value) {
      currentSession.value.messages = []
    }
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
      
      // TODO: Implement API call to load message history
      // For now, we'll just clear messages as if starting fresh
      clearMessages()
      
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
    addMessage,
    addUserMessage,
    addNoahMessage,
    addStreamingMessage,
    updateStreamingMessage,
    finalizeStreamingMessage,
    clearMessages,
    setLoading,
    setError,
    loadMessageHistory
  }
})