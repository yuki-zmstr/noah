import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { 
  PreferenceTransparency, 
  PreferenceModel, 
  LanguageReadingLevels, 
  PreferenceOverride,
  PreferenceEvolution
} from '@/types/preferences'
import { preferenceUpdateService, type PreferenceUpdateImpact } from '@/services/preferenceUpdateService'

export const usePreferencesStore = defineStore('preferences', () => {
  // State
  const transparencyData = ref<PreferenceTransparency | null>(null)
  const evolutionData = ref<PreferenceEvolution | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdated = ref<Date | null>(null)

  // Getters
  const hasTransparencyData = computed(() => transparencyData.value !== null)
  const hasEvolutionData = computed(() => evolutionData.value !== null)
  
  const topicPreferences = computed(() => 
    transparencyData.value?.topic_preferences || []
  )
  
  const contentTypePreferences = computed(() => 
    transparencyData.value?.content_type_preferences || []
  )
  
  const contextualPreferences = computed(() => 
    transparencyData.value?.contextual_patterns || []
  )
  
  const readingLevels = computed(() => 
    transparencyData.value?.reading_levels || null
  )

  const strongTopicPreferences = computed(() => 
    topicPreferences.value.filter(tp => Math.abs(tp.weight) > 0.6)
  )

  const moderateTopicPreferences = computed(() => 
    topicPreferences.value.filter(tp => Math.abs(tp.weight) > 0.3 && Math.abs(tp.weight) <= 0.6)
  )

  const weakTopicPreferences = computed(() => 
    topicPreferences.value.filter(tp => Math.abs(tp.weight) <= 0.3)
  )

  // Actions
  const fetchTransparencyData = async (userId: string) => {
    try {
      isLoading.value = true
      error.value = null

      const response = await fetch(`/api/v1/preferences/${userId}/transparency`)
      if (!response.ok) {
        throw new Error(`Failed to fetch transparency data: ${response.statusText}`)
      }

      transparencyData.value = await response.json()
      lastUpdated.value = new Date()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch transparency data'
      console.error('Error fetching transparency data:', err)
    } finally {
      isLoading.value = false
    }
  }

  const fetchEvolutionData = async (userId: string) => {
    try {
      isLoading.value = true
      error.value = null

      const response = await fetch(`/api/v1/preferences/${userId}/evolution`)
      if (!response.ok) {
        throw new Error(`Failed to fetch evolution data: ${response.statusText}`)
      }

      evolutionData.value = await response.json()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch evolution data'
      console.error('Error fetching evolution data:', err)
    } finally {
      isLoading.value = false
    }
  }

  const updatePreferences = async (userId: string, preferences: PreferenceModel) => {
    try {
      isLoading.value = true
      error.value = null

      const response = await fetch(`/api/v1/preferences/${userId}/preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferences),
      })

      if (!response.ok) {
        throw new Error(`Failed to update preferences: ${response.statusText}`)
      }

      const result = await response.json()
      
      // Update local state with new transparency data
      if (result.updated_preferences) {
        transparencyData.value = result.updated_preferences
        lastUpdated.value = new Date()
      }

      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update preferences'
      console.error('Error updating preferences:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const updateReadingLevels = async (userId: string, readingLevels: LanguageReadingLevels) => {
    try {
      isLoading.value = true
      error.value = null

      const response = await fetch(`/api/v1/preferences/${userId}/reading-levels`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(readingLevels),
      })

      if (!response.ok) {
        throw new Error(`Failed to update reading levels: ${response.statusText}`)
      }

      const result = await response.json()
      
      // Update local state
      if (transparencyData.value) {
        transparencyData.value.reading_levels = result.updated_reading_levels
        lastUpdated.value = new Date()
      }

      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update reading levels'
      console.error('Error updating reading levels:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const overridePreference = async (userId: string, override: PreferenceOverride): Promise<PreferenceUpdateImpact[]> => {
    try {
      // Use the HTTP preference update service for real-time updates with impact analysis
      return await preferenceUpdateService.updatePreferenceWithImpact(userId, override)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to override preference'
      console.error('Error overriding preference:', err)
      throw err
    }
  }

  const updateReadingLevelsWithImpact = async (userId: string, language: 'english' | 'japanese', newLevel: number): Promise<PreferenceUpdateImpact[]> => {
    try {
      return await preferenceUpdateService.updateReadingLevelWithImpact(userId, language, newLevel)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update reading level'
      console.error('Error updating reading level:', err)
      throw err
    }
  }

  const refreshData = async (userId: string) => {
    await Promise.all([
      fetchTransparencyData(userId),
      fetchEvolutionData(userId)
    ])
  }

  const clearData = () => {
    transparencyData.value = null
    evolutionData.value = null
    error.value = null
    lastUpdated.value = null
  }

  const setError = (errorMessage: string | null) => {
    error.value = errorMessage
  }

  return {
    // State
    transparencyData,
    evolutionData,
    isLoading,
    error,
    lastUpdated,

    // Getters
    hasTransparencyData,
    hasEvolutionData,
    topicPreferences,
    contentTypePreferences,
    contextualPreferences,
    readingLevels,
    strongTopicPreferences,
    moderateTopicPreferences,
    weakTopicPreferences,

    // Actions
    fetchTransparencyData,
    fetchEvolutionData,
    updatePreferences,
    updateReadingLevels,
    overridePreference,
    updateReadingLevelsWithImpact,
    refreshData,
    clearData,
    setError
  }
})