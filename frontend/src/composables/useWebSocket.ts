import { ref, onMounted, onUnmounted } from 'vue'
import type { ChatMessage, TypingIndicator } from '@/types/chat'

export function useWebSocket(serverUrl: string = 'ws://localhost:8000') {
  const socket = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const connectionError = ref<string | null>(null)
  const connectionId = ref<string>(`conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)

  const connect = () => {
    try {
      const wsUrl = `${serverUrl}/api/v1/chat/ws/${connectionId.value}`
      socket.value = new WebSocket(wsUrl)

      socket.value.onopen = () => {
        isConnected.value = true
        connectionError.value = null
        console.log('WebSocket connected')
      }

      socket.value.onclose = () => {
        isConnected.value = false
        console.log('WebSocket disconnected')
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
  }

  const handleMessage = (data: any) => {
    const { type } = data
    if (messageHandlers[type as keyof typeof messageHandlers]) {
      messageHandlers[type as keyof typeof messageHandlers].forEach((handler: any) => handler(data))
    }
  }

  const sendMessage = (message: string, sessionId: string) => {
    if (socket.value && isConnected.value) {
      const payload = {
        type: 'user_message',
        content: message,
        sessionId,
        timestamp: new Date().toISOString()
      }
      socket.value.send(JSON.stringify(payload))
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

  const joinSession = (sessionId: string, userId: string) => {
    if (socket.value && isConnected.value) {
      const payload = {
        type: 'join_session',
        sessionId,
        userId
      }
      socket.value.send(JSON.stringify(payload))
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
    joinSession
  }
}