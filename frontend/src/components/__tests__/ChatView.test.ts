import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '@/views/ChatView.vue'
import { useChatStore } from '@/stores/chat'

// Mock WebSocket
vi.mock('@/composables/useWebSocket', () => ({
  useWebSocket: () => ({
    isConnected: { value: true },
    connectionError: { value: null },
    sendMessage: vi.fn(),
    onMessage: vi.fn(),
    onMessageChunk: vi.fn(),
    onRecommendations: vi.fn(),
    onPurchaseLinks: vi.fn(),
    onMessageComplete: vi.fn(),
    onTyping: vi.fn(),
    onConversationHistory: vi.fn(),
    joinSession: vi.fn(),
  })
}))

describe('ChatView Reactivity', () => {
  let router: any

  beforeEach(() => {
    setActivePinia(createPinia())
    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', component: ChatView },
        { path: '/preferences', component: { template: '<div>Preferences</div>' } }
      ]
    })
  })

  it('shows welcome message when no messages exist', async () => {
    const wrapper = mount(ChatView, {
      global: {
        plugins: [router]
      }
    })

    const chatStore = useChatStore()
    chatStore.initializeSession('test_user')

    await wrapper.vm.$nextTick()

    // Should show welcome message when no messages
    expect(wrapper.text()).toContain('Start a conversation with Noah')
  })

  it('hides welcome message when messages exist', async () => {
    const wrapper = mount(ChatView, {
      global: {
        plugins: [router]
      }
    })

    const chatStore = useChatStore()
    chatStore.initializeSession('test_user')

    await wrapper.vm.$nextTick()

    // Initially shows welcome message
    expect(wrapper.text()).toContain('Start a conversation with Noah')

    // Add a message
    chatStore.addUserMessage('Hello!')

    await wrapper.vm.$nextTick()

    // Welcome message should be hidden
    expect(wrapper.text()).not.toContain('Start a conversation with Noah')
  })

  it('displays messages reactively', async () => {
    const wrapper = mount(ChatView, {
      global: {
        plugins: [router]
      }
    })

    const chatStore = useChatStore()
    chatStore.initializeSession('test_user')

    await wrapper.vm.$nextTick()

    // Add messages
    chatStore.addUserMessage('Hello Noah!')
    chatStore.addNoahMessage('Hello there!')

    await wrapper.vm.$nextTick()

    // Should display both messages
    expect(wrapper.text()).toContain('Hello Noah!')
    expect(wrapper.text()).toContain('Hello there!')
  })

  it('shows loading state reactively', async () => {
    const wrapper = mount(ChatView, {
      global: {
        plugins: [router]
      }
    })

    const chatStore = useChatStore()
    chatStore.initializeSession('test_user')

    await wrapper.vm.$nextTick()

    // Initially not loading
    expect(wrapper.find('.animate-spin').exists()).toBe(false)

    // Set loading state
    chatStore.setLoading(true)

    await wrapper.vm.$nextTick()

    // Should show loading spinner
    expect(wrapper.find('.animate-spin').exists()).toBe(true)
  })

  it('shows error state reactively', async () => {
    const wrapper = mount(ChatView, {
      global: {
        plugins: [router]
      }
    })

    const chatStore = useChatStore()
    chatStore.initializeSession('test_user')

    await wrapper.vm.$nextTick()

    // Initially no error
    expect(wrapper.find('.bg-red-50').exists()).toBe(false)

    // Set error state
    chatStore.setError('Test error message')

    await wrapper.vm.$nextTick()

    // Should show error message
    expect(wrapper.find('.bg-red-50').exists()).toBe(true)
    expect(wrapper.text()).toContain('Test error message')
  })
})