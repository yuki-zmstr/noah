import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import LanguageToggle from '../LanguageToggle.vue'
import { useLanguageStore } from '@/stores/language'

describe('LanguageToggle', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders with English by default', () => {
    const wrapper = mount(LanguageToggle)
    expect(wrapper.text()).toContain('English')
    expect(wrapper.text()).toContain('🇺🇸')
  })

  it('toggles to Japanese when clicked', async () => {
    const wrapper = mount(LanguageToggle)
    const languageStore = useLanguageStore()
    
    // Initially English
    expect(languageStore.currentLanguage).toBe('english')
    expect(wrapper.text()).toContain('English')
    
    // Click to toggle
    await wrapper.find('button').trigger('click')
    
    // Should now be Japanese
    expect(languageStore.currentLanguage).toBe('japanese')
    expect(wrapper.text()).toContain('日本語')
    expect(wrapper.text()).toContain('🇯🇵')
  })

  it('toggles back to English when clicked again', async () => {
    const wrapper = mount(LanguageToggle)
    const languageStore = useLanguageStore()
    
    // Start with Japanese
    languageStore.setLanguage('japanese')
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('日本語')
    
    // Click to toggle back
    await wrapper.find('button').trigger('click')
    
    // Should now be English
    expect(languageStore.currentLanguage).toBe('english')
    expect(wrapper.text()).toContain('English')
  })

  it('has correct title attributes', async () => {
    const wrapper = mount(LanguageToggle)
    const languageStore = useLanguageStore()
    
    // English state
    expect(wrapper.find('button').attributes('title')).toBe('Switch to Japanese')
    
    // Toggle to Japanese
    languageStore.setLanguage('japanese')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('button').attributes('title')).toBe('Switch to English')
  })
})