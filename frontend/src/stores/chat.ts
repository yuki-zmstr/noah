import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, ChatSession } from '@/types/chat'
import { useAuthStore } from '@/stores/auth'

// Debounce utility for localStorage saves
let saveTimeout: NodeJS.Timeout | null = null
const debouncedSave = (userId: string, saveFunction: (userId: string) => void) => {
  if (saveTimeout) {
    clearTimeout(saveTimeout)
  }
  saveTimeout = setTimeout(() => {
    saveFunction(userId)
    saveTimeout = null
  }, 500) // Save after 500ms of inactivity
}

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
      // Create a clean version of messages for storage (remove non-serializable data like Sets)
      const cleanMessages = messages.value.map(msg => ({
        ...msg,
        metadata: msg.metadata ? {
          ...msg.metadata,
          processedChunks: undefined // Don't save chunk tracking data
        } : undefined
      }))
      localStorage.setItem(storageKey, JSON.stringify(cleanMessages))
    } catch (err) {
      console.error('Failed to save user messages:', err)
    }
  }

  const addMessage = (message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const authStore = useAuthStore()
    
    const newMessage: ChatMessage = {
      ...message,
      id: `msg_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`,
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
      id: `msg_streaming_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`,
      content,
      sender: 'noah',
      type,
      timestamp: new Date(),
      metadata: {
        isStreaming: true,
        processedChunks: new Set<string>() // Track processed chunks to prevent duplicates
      }
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
        messages.value[messageIndex].metadata = { ...messages.value[messageIndex].metadata, ...metadata }
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
            currentSession.value.messages[sessionMessageIndex].metadata = { 
              ...currentSession.value.messages[sessionMessageIndex].metadata, 
              ...metadata 
            }
          }
        }
      }
      
      // Save updated messages for the current user (debounced during streaming)
      if (authStore.userId) {
        const message = messages.value[messageIndex]
        if (message.metadata?.isStreaming) {
          debouncedSave(authStore.userId, saveUserMessages)
        } else {
          saveUserMessages(authStore.userId)
        }
      }
    }
  }

  const appendToStreamingMessage = (messageId: string, content: string, metadata?: ChatMessage['metadata']) => {
    const messageIndex = messages.value.findIndex(msg => msg.id === messageId)
    if (messageIndex !== -1) {
      const message = messages.value[messageIndex]
      const processedChunks = message.metadata?.processedChunks as Set<string> || new Set<string>()
      
      // Generate chunk ID - prefer sequence number if available, otherwise use content hash
      let chunkId: string
      if (metadata?.sequence !== undefined) {
        chunkId = `seq_${metadata.sequence}`
      } else {
        const contentHash = content.split('').reduce((hash, char) => {
          return ((hash << 5) - hash) + char.charCodeAt(0)
        }, 0)
        chunkId = `${Date.now()}_${Math.abs(contentHash)}_${content.length}`
      }

      // Check if this chunk has already been processed
      if (processedChunks.has(chunkId)) {
        console.warn(`[chat.ts] Duplicate chunk detected and skipped: ${chunkId}`)
        return
      }
      
      // Mark chunk as processed
      processedChunks.add(chunkId)
      
      // Update the message with the new chunk
      updateStreamingMessage(messageId, content, { 
        ...metadata, 
        processedChunks 
      }, true)
    }
  }

  const finalizeStreamingMessage = (messageId: string, finalContent?: string, metadata?: ChatMessage['metadata']) => {
    // If finalContent is provided, replace the entire content (for cases where backend sends complete message)
    // Otherwise, just mark as finalized (content was already accumulated via chunks)
    const messageIndex = messages.value.findIndex(msg => msg.id === messageId)

    if (messageIndex !== -1) {
      const finalMetadata = {
        ...messages.value[messageIndex].metadata,
        ...metadata,
        isStreaming: false,
        processedChunks: undefined // Clear chunk tracking data
      }

      if (finalContent) {
        // Replace with final content
        updateStreamingMessage(messageId, finalContent, finalMetadata, false)
      } else {
        // Just update metadata without changing content
        messages.value[messageIndex].metadata = finalMetadata

        // Update in session as well
        if (currentSession.value) {
          const sessionMessageIndex = currentSession.value.messages.findIndex(msg => msg.id === messageId)
          if (sessionMessageIndex !== -1) {
            currentSession.value.messages[sessionMessageIndex].metadata = finalMetadata
          }
        }

        // Save updated messages
        const authStore = useAuthStore()
        if (authStore.userId) {
          saveUserMessages(authStore.userId)
        }
      }
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