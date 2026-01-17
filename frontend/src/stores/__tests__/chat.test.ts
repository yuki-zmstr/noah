import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '../chat'

describe('Chat Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes session correctly', () => {
    const store = useChatStore()
    const userId = 'test_user'
    
    store.initializeSession(userId)
    
    expect(store.currentSession).toBeTruthy()
    expect(store.currentSession?.userId).toBe(userId)
    expect(store.currentSession?.sessionId).toContain('session_test_user_')
    expect(store.messages).toEqual([])
  })

  it('adds user message correctly', () => {
    const store = useChatStore()
    store.initializeSession('test_user')
    
    const message = store.addUserMessage('Hello Noah!')
    
    expect(store.messages).toHaveLength(1)
    expect(message.content).toBe('Hello Noah!')
    expect(message.sender).toBe('user')
    expect(message.type).toBe('text')
    expect(message.id).toBeTruthy()
  })

  it('adds Noah message correctly', () => {
    const store = useChatStore()
    store.initializeSession('test_user')
    
    const message = store.addNoahMessage('Hello there!', 'text')
    
    expect(store.messages).toHaveLength(1)
    expect(message.content).toBe('Hello there!')
    expect(message.sender).toBe('noah')
    expect(message.type).toBe('text')
  })

  it('sorts messages by timestamp', () => {
    const store = useChatStore()
    store.initializeSession('test_user')
    
    // Add messages with slight delay to ensure different timestamps
    const msg1 = store.addUserMessage('First message')
    setTimeout(() => {
      const msg2 = store.addNoahMessage('Second message')
      
      const sorted = store.sortedMessages
      expect(sorted[0].id).toBe(msg1.id)
      expect(sorted[1].id).toBe(msg2.id)
    }, 1)
  })

  it('clears messages correctly', () => {
    const store = useChatStore()
    store.initializeSession('test_user')
    
    store.addUserMessage('Test message')
    expect(store.messages).toHaveLength(1)
    
    store.clearMessages()
    expect(store.messages).toHaveLength(0)
  })

  it('manages loading state', () => {
    const store = useChatStore()
    
    expect(store.isLoading).toBe(false)
    
    store.setLoading(true)
    expect(store.isLoading).toBe(true)
    
    store.setLoading(false)
    expect(store.isLoading).toBe(false)
  })

  it('manages error state', () => {
    const store = useChatStore()
    
    expect(store.error).toBe(null)
    
    store.setError('Test error')
    expect(store.error).toBe('Test error')
    
    store.setError(null)
    expect(store.error).toBe(null)
  })
})