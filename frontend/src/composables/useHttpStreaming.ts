import { ref } from 'vue'
import type { ChatMessage } from '@/types/chat'
import { awsConfig } from '@/config/aws-config'

export function useHttpStreaming() {
  const isStreaming = ref(false)
  const streamError = ref<string | null>(null)

  // Message handlers
  const messageHandlers = {
    content_chunk: [] as Array<(chunk: { content: string, is_final: boolean, timestamp: string, sequence?: number }) => void>,
    recommendations: [] as Array<(data: { recommendations: any[], timestamp: string }) => void>,
    complete: [] as Array<(data: { message_id: string, timestamp: string }) => void>,
    error: [] as Array<(data: { content: string, timestamp: string }) => void>,
  }

  const sendMessage = async (
    message: string,
    sessionId: string,
    userId: string,
    metadata?: any
  ): Promise<void> => {
    try {
      isStreaming.value = true
      streamError.value = null

      // Create AbortController for timeout handling
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 600000) // 10 minutes timeout

      const response = await fetch(`${awsConfig.apiEndpoint}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          session_id: sessionId,
          user_id: userId,
          metadata
        }),
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body reader available')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      try {
        while (true) {
          const { done, value } = await reader.read()
          
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          
          // Process complete lines
          const lines = buffer.split('\n')
          buffer = lines.pop() || '' // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6)) // Remove 'data: ' prefix
                handleStreamMessage(data)
              } catch (parseError) {
                console.error('Error parsing stream data:', parseError, line)
              }
            }
          }
        }
      } finally {
        reader.releaseLock()
      }

    } catch (error) {
      console.error('Streaming error:', error)
      streamError.value = error instanceof Error ? error.message : 'Unknown streaming error'
      
      // Notify error handlers
      messageHandlers.error.forEach(handler => 
        handler({
          content: streamError.value || 'Unknown error occurred',
          timestamp: new Date().toISOString()
        })
      )
    } finally {
      isStreaming.value = false
    }
  }

  const handleStreamMessage = (data: any) => {
    const { type } = data
    
    if (messageHandlers[type as keyof typeof messageHandlers]) {
      messageHandlers[type as keyof typeof messageHandlers].forEach((handler: any) => handler(data))
    } else {
      console.warn('Unknown stream message type:', type)
    }
  }

  const getConversationHistory = async (sessionId: string, limit: number = 50): Promise<ChatMessage[]> => {
    try {
      const response = await fetch(`${awsConfig.apiEndpoint}/api/v1/chat/history`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          limit
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      if (result.status === 'success') {
        return result.messages.map((msg: any) => ({
          id: msg.message_id,
          content: msg.content,
          sender: msg.sender,
          type: msg.sender === 'noah' && msg.recommendations ? 'recommendation' : 'text',
          timestamp: new Date(msg.timestamp),
          metadata: {
            recommendations: msg.recommendations,
            intent: msg.intent
          }
        }))
      } else {
        throw new Error('Failed to load conversation history')
      }

    } catch (error) {
      console.error('Error loading conversation history:', error)
      throw error
    }
  }

  const updatePreferences = async (userId: string, preferenceData: any): Promise<any> => {
    try {
      const response = await fetch(`${awsConfig.apiEndpoint}/api/v1/chat/preferences/update?user_id=${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferenceData)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()

    } catch (error) {
      console.error('Error updating preferences:', error)
      throw error
    }
  }

  // Event handlers - return unsubscribe functions to allow cleanup
  const onContentChunk = (callback: (chunk: { content: string, is_final: boolean, timestamp: string, sequence?: number }) => void) => {
    messageHandlers.content_chunk.push(callback)
    return () => {
      const index = messageHandlers.content_chunk.indexOf(callback)
      if (index > -1) {
        messageHandlers.content_chunk.splice(index, 1)
      }
    }
  }

  const onRecommendations = (callback: (data: { recommendations: any[], timestamp: string }) => void) => {
    messageHandlers.recommendations.push(callback)
    return () => {
      const index = messageHandlers.recommendations.indexOf(callback)
      if (index > -1) {
        messageHandlers.recommendations.splice(index, 1)
      }
    }
  }

  const onComplete = (callback: (data: { message_id: string, timestamp: string }) => void) => {
    messageHandlers.complete.push(callback)
    return () => {
      const index = messageHandlers.complete.indexOf(callback)
      if (index > -1) {
        messageHandlers.complete.splice(index, 1)
      }
    }
  }

  const onError = (callback: (data: { content: string, timestamp: string }) => void) => {
    messageHandlers.error.push(callback)
    return () => {
      const index = messageHandlers.error.indexOf(callback)
      if (index > -1) {
        messageHandlers.error.splice(index, 1)
      }
    }
  }

  // Cleanup function to remove all handlers
  const cleanup = () => {
    messageHandlers.content_chunk = []
    messageHandlers.recommendations = []
    messageHandlers.complete = []
    messageHandlers.error = []
  }

  return {
    isStreaming,
    streamError,
    sendMessage,
    getConversationHistory,
    updatePreferences,
    onContentChunk,
    onRecommendations,
    onComplete,
    onError,
    cleanup
  }
}