import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatMessage from '../ChatMessage.vue'
import type { ChatMessage as ChatMessageType } from '@/types/chat'

describe('ChatMessage', () => {
  const mockTextMessage: ChatMessageType = {
    id: 'msg_1',
    content: 'Hello, Noah!',
    sender: 'user',
    timestamp: new Date('2024-01-01T12:00:00Z'),
    type: 'text'
  }

  const mockRecommendationMessage: ChatMessageType = {
    id: 'msg_2',
    content: 'Here are some book recommendations:',
    sender: 'noah',
    timestamp: new Date('2024-01-01T12:01:00Z'),
    type: 'recommendation',
    metadata: {
      recommendations: [
        {
          id: 'book_1',
          title: 'Test Book',
          author: 'Test Author',
          description: 'A test book description',
          interestScore: 0.9,
          readingLevel: 'Intermediate',
          estimatedReadingTime: 300
        }
      ]
    }
  }

  it('renders text message correctly', () => {
    const wrapper = mount(ChatMessage, {
      props: { message: mockTextMessage }
    })

    expect(wrapper.text()).toContain('Hello, Noah!')
    expect(wrapper.find('.chat-message-user').exists()).toBe(true)
  })

  it('renders Noah message correctly', () => {
    const noahMessage = { ...mockTextMessage, sender: 'noah' as const }
    const wrapper = mount(ChatMessage, {
      props: { message: noahMessage }
    })

    expect(wrapper.find('.chat-message-noah').exists()).toBe(true)
  })

  it('renders recommendation message with book details', () => {
    const wrapper = mount(ChatMessage, {
      props: { message: mockRecommendationMessage }
    })

    expect(wrapper.text()).toContain('Here are some book recommendations:')
    expect(wrapper.text()).toContain('Test Book')
    expect(wrapper.text()).toContain('Test Author')
    expect(wrapper.text()).toContain('A test book description')
    expect(wrapper.text()).toContain('Intermediate')
  })

  it('formats timestamp correctly', () => {
    const wrapper = mount(ChatMessage, {
      props: { message: mockTextMessage }
    })

    // Should contain formatted time (any valid time format)
    expect(wrapper.text()).toMatch(/\d{1,2}:\d{2}\s*(AM|PM)/i)
  })
})