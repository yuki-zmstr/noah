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

  it('opens dropdown when main button is clicked', async () => {
    const wrapper = mount(LanguageToggle)
    
    // Initially dropdown should be closed
    expect(wrapper.find('.absolute').exists()).toBe(false)
    
    // Click main button to open dropdown
    await wrapper.find('button').trigger('click')
    
    // Dropdown should now be visible
    expect(wrapper.find('.absolute').exists()).toBe(true)
    expect(wrapper.text()).toContain('English')
    expect(wrapper.text()).toContain('日本語')
  })

  it('switches to Japanese when Japanese option is clicked', async () => {
    const wrapper = mount(LanguageToggle)
    const languageStore = useLanguageStore()
    
    // Initially English
    expect(languageStore.currentLanguage).toBe('english')
    
    // Open dropdown
    await wrapper.find('button').trigger('click')
    
    // Click Japanese option
    const japaneseButton = wrapper.findAll('button').find(btn => 
      btn.text().includes('日本語')
    )
    await japaneseButton?.trigger('click')
    
    // Should now be Japanese
    expect(languageStore.currentLanguage).toBe('japanese')
    
    // Dropdown should be closed
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.absolute').exists()).toBe(false)
  })

  it('switches to English when English option is clicked', async () => {
    const wrapper = mount(LanguageToggle)
    const languageStore = useLanguageStore()
    
    // Start with Japanese
    languageStore.setLanguage('japanese')
    await wrapper.vm.$nextTick()
    
    // Open dropdown
    await wrapper.find('button').trigger('click')
    
    // Click English option
    const englishButton = wrapper.findAll('button').find(btn => 
      btn.text().includes('English') && !btn.text().includes('日本語')
    )
    await englishButton?.trigger('click')
    
    // Should now be English
    expect(languageStore.currentLanguage).toBe('english')
    
    // Dropdown should be closed
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.absolute').exists()).toBe(false)
  })

  it('shows checkmark for currently selected language', async () => {
    const wrapper = mount(LanguageToggle)
    const languageStore = useLanguageStore()
    
    // Open dropdown
    await wrapper.find('button').trigger('click')
    
    // English should have checkmark (default)
    const englishButton = wrapper.findAll('button').find(btn => 
      btn.text().includes('English') && !btn.text().includes('日本語')
    )
    expect(englishButton?.find('svg').exists()).toBe(true)
    
    // Switch to Japanese
    const japaneseButton = wrapper.findAll('button').find(btn => 
      btn.text().includes('日本語')
    )
    await japaneseButton?.trigger('click')
    
    // Open dropdown again
    await wrapper.find('button').trigger('click')
    
    // Japanese should now have checkmark
    const japaneseButtonAfter = wrapper.findAll('button').find(btn => 
      btn.text().includes('日本語')
    )
    expect(japaneseButtonAfter?.find('svg').exists()).toBe(true)
  })

  it('has correct title attribute', () => {
    const wrapper = mount(LanguageToggle)
    expect(wrapper.find('button').attributes('title')).toBe('Select language')
  })
})