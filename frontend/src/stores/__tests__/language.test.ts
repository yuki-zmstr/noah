import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useLanguageStore } from '../language'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
vi.stubGlobal('localStorage', localStorageMock)

describe('Language Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('initializes with English by default', () => {
    const store = useLanguageStore()
    expect(store.currentLanguage).toBe('english')
    expect(store.isEnglish).toBe(true)
    expect(store.isJapanese).toBe(false)
    expect(store.languageLabel).toBe('English')
  })

  it('sets language correctly', () => {
    const store = useLanguageStore()
    
    store.setLanguage('japanese')
    
    expect(store.currentLanguage).toBe('japanese')
    expect(store.isEnglish).toBe(false)
    expect(store.isJapanese).toBe(true)
    expect(store.languageLabel).toBe('日本語')
    expect(localStorageMock.setItem).toHaveBeenCalledWith('noah-language', 'japanese')
  })

  it('toggles language correctly', () => {
    const store = useLanguageStore()
    
    // Start with English, toggle to Japanese
    store.toggleLanguage()
    expect(store.currentLanguage).toBe('japanese')
    expect(localStorageMock.setItem).toHaveBeenCalledWith('noah-language', 'japanese')
    
    // Toggle back to English
    store.toggleLanguage()
    expect(store.currentLanguage).toBe('english')
    expect(localStorageMock.setItem).toHaveBeenCalledWith('noah-language', 'english')
  })

  it('initializes from localStorage', () => {
    localStorageMock.getItem.mockReturnValue('japanese')
    
    const store = useLanguageStore()
    store.initializeLanguage()
    
    expect(store.currentLanguage).toBe('japanese')
    expect(localStorageMock.getItem).toHaveBeenCalledWith('noah-language')
  })

  it('ignores invalid localStorage values', () => {
    localStorageMock.getItem.mockReturnValue('invalid-language')
    
    const store = useLanguageStore()
    store.initializeLanguage()
    
    // Should remain English (default)
    expect(store.currentLanguage).toBe('english')
  })

  it('handles null localStorage values', () => {
    localStorageMock.getItem.mockReturnValue(null)
    
    const store = useLanguageStore()
    store.initializeLanguage()
    
    // Should remain English (default)
    expect(store.currentLanguage).toBe('english')
  })
})