import { ref, onMounted, onUnmounted } from 'vue'
import type { ChatMessage, TypingIndicator } from '@/types/chat'
import { awsConfig } from '@/config/aws-config'

export function useWebSocket() {
  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const connectionError = ref<string | null>(null)
  const connectionId = ref<string>(`conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)

  const connect = () => {
    try {
      // Convert HTTP endpoint to WebSocket URL
      const apiEndpoint = awsConfig.apiEndpoint
      const wsUrl = apiEndpoint.replace(/^http/, 'ws') + `/api/v1/chat/ws/${connectionId.value}`
      
      console.log('Connecting to WebSocket:', wsUrl)
      socket.value = new WebSocket(wsUrl)

      socket.value.onopen = () => {
        isConnected.value = true
        connectionError.value = null
        console.log('WebSocket connected to:', wsUrl)
      }

      socket.value.onclose = (event) => {
        isConnected.value = false
        console.log('WebSocket disconnected:', event.code, event.reason)
        
        // Attempt to reconnect after a delay if not a normal closure
        if (event.code !== 1000) {
          setTimeout(() => {
            if (!isConnected.value) {
              console.log('Attempting to reconnect...')
              connect()
            }
          }, 3000)
        }
      }

      socket.value.onerror = (error) => {
        connectionError.value = 'WebSocket connection error'
        console.error('WebSocket connection error:', error)
      }

      socket.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleMessage(data)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

    } catch (error) {
      connectionError.value = error instanceof Error ? error.message : 'Unknown connection error'
    }
  }

  const disconnect = () => {
    if (socket.value) {
      socket.value.close()
      socket.value = null
      isConnected.value = false
    }
  }

  // Message handlers
  const messageHandlers = {
    noah_message: [] as Array<(message: ChatMessage) => void>,
    noah_message_chunk: [] as Array<(chunk: { content: string, is_final: boolean, timestamp: string }) => void>,
    noah_recommendations: [] as Array<(data: { recommendations: any[], is_discovery?: boolean, timestamp: string }) => void>,
    noah_purchase_links: [] as Array<(data: { purchase_links: any[], timestamp: string }) => void>,
    noah_message_complete: [] as Array<(data: { message_id: string, timestamp: string }) => void>,
    typing: [] as Array<(typing: TypingIndicator) => void>,
    conversation_history: [] as Array<(data: { messages: ChatMessage[] }) => void>,
    preference_update: [] as Array<(data: { user_id: string, updated_preferences: any, timestamp: string }) => void>,
    recommendation_refresh: [] as Array<(data: { user_id: string, new_recommendations: any[], timestamp: string }) => void>,
  }

  const handleMessage = (data: any) => {
    const { type } = data
    console.log('Received WebSocket message:', type, data)
    
    if (messageHandlers[type as keyof typeof messageHandlers]) {
      messageHandlers[type as keyof typeof messageHandlers].forEach((handler: any) => handler(data))
    } else {
      console.warn('Unknown message type received:', type)
    }
  }

  const sendMessage = (message: string, sessionId: string, metadata?: any) => {
    if (socket.value && isConnected.value) {
      const payload = {
        type: 'user_message',
        content: message,
        sessionId,
        timestamp: new Date().toISOString(),
        metadata
      }
      console.log('Sending message:', payload)
      socket.value.send(JSON.stringify(payload))
    } else {
      console.error('Cannot send message: WebSocket not connected')
      connectionError.value = 'Not connected to server'
    }
  }

  const onMessage = (callback: (message: ChatMessage) => void) => {
    messageHandlers.noah_message.push(callback)
  }

  const onMessageChunk = (callback: (chunk: { content: string, is_final: boolean, timestamp: string }) => void) => {
    messageHandlers.noah_message_chunk.push(callback)
  }

  const onRecommendations = (callback: (data: { recommendations: any[], is_discovery?: boolean, timestamp: string }) => void) => {
    messageHandlers.noah_recommendations.push(callback)
  }

  const onPurchaseLinks = (callback: (data: { purchase_links: any[], timestamp: string }) => void) => {
    messageHandlers.noah_purchase_links.push(callback)
  }

  const onMessageComplete = (callback: (data: { message_id: string, timestamp: string }) => void) => {
    messageHandlers.noah_message_complete.push(callback)
  }

  const onTyping = (callback: (typing: TypingIndicator) => void) => {
    messageHandlers.typing.push(callback)
  }

  const onConversationHistory = (callback: (data: { messages: ChatMessage[] }) => void) => {
    messageHandlers.conversation_history.push(callback)
  }

  const onPreferenceUpdate = (callback: (data: { user_id: string, updated_preferences: any, timestamp: string }) => void) => {
    messageHandlers.preference_update.push(callback)
  }

  const onRecommendationRefresh = (callback: (data: { user_id: string, new_recommendations: any[], timestamp: string }) => void) => {
    messageHandlers.recommendation_refresh.push(callback)
  }

  const sendPreferenceUpdate = (userId: string, preferenceData: any) => {
    if (socket.value && isConnected.value) {
      const payload = {
        type: 'preference_update',
        userId,
        preferenceData,
        timestamp: new Date().toISOString()
      }
      console.log('Sending preference update:', payload)
      socket.value.send(JSON.stringify(payload))
    } else {
      console.error('Cannot send preference update: WebSocket not connected')
    }
  }

  const joinSession = (sessionId: string, userId: string) => {
    if (socket.value && isConnected.value) {
      const payload = {
        type: 'join_session',
        sessionId,
        userId,
        timestamp: new Date().toISOString()
      }
      console.log('Joining session:', payload)
      socket.value.send(JSON.stringify(payload))
    } else {
      console.error('Cannot join session: WebSocket not connected')
    }
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    socket,
    isConnected,
    connectionError,
    connect,
    disconnect,
    sendMessage,
    onMessage,
    onMessageChunk,
    onRecommendations,
    onPurchaseLinks,
    onMessageComplete,
    onTyping,
    onConversationHistory,
    onPreferenceUpdate,
    onRecommendationRefresh,
    sendPreferenceUpdate,
    joinSession
  }
}