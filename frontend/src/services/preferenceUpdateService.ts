import { usePreferencesStore } from '@/stores/preferences'
import { useChatStore } from '@/stores/chat'
import { useWebSocket } from '@/composables/useWebSocket'
import type { PreferenceOverride, PreferenceTransparency } from '@/types/preferences'

export interface PreferenceUpdateImpact {
  type: 'topic' | 'content_type' | 'reading_level'
  item: string
  oldValue: number
  newValue: number
  change: number
  impactDescription: string
  affectedRecommendations?: number
}

export class PreferenceUpdateService {
  private preferencesStore = usePreferencesStore()
  private chatStore = useChatStore()
  private webSocket = useWebSocket()

  constructor() {
    this.setupWebSocketListeners()
  }

  private setupWebSocketListeners() {
    // Listen for preference update confirmations from backend
    this.webSocket.onPreferenceUpdate((data) => {
      this.handlePreferenceUpdateNotification(data)
    })

    // Listen for recommendation refreshes
    this.webSocket.onRecommendationRefresh((data) => {
      this.handleRecommendationRefresh(data)
    })
  }

  async updatePreferenceWithImpact(
    userId: string, 
    override: PreferenceOverride
  ): Promise<PreferenceUpdateImpact[]> {
    try {
      // Calculate impact before update
      const impactAnalysis = this.calculatePreferenceImpact(override)
      
      // Update preference via API
      const result = await this.preferencesStore.overridePreference(userId, override)
      
      // Send real-time update via WebSocket for immediate recommendation refresh
      this.webSocket.sendPreferenceUpdate(userId, {
        override,
        impact: impactAnalysis
      })

      // Add impact message to chat
      this.addImpactMessageToChat(override, impactAnalysis)

      return impactAnalysis
    } catch (error) {
      console.error('Failed to update preference with impact:', error)
      throw error
    }
  }

  async updateReadingLevelWithImpact(
    userId: string,
    language: 'english' | 'japanese',
    newLevel: number
  ): Promise<PreferenceUpdateImpact[]> {
    try {
      const currentLevels = this.preferencesStore.readingLevels
      if (!currentLevels) throw new Error('No reading levels available')

      const oldLevel = currentLevels[language].level
      const impact = this.calculateReadingLevelImpact(language, oldLevel, newLevel)

      // Update reading level
      const updatedLevels = { ...currentLevels }
      updatedLevels[language] = {
        ...updatedLevels[language],
        level: newLevel
      }

      await this.preferencesStore.updateReadingLevels(userId, updatedLevels)

      // Send real-time update
      this.webSocket.sendPreferenceUpdate(userId, {
        type: 'reading_level',
        language,
        oldLevel,
        newLevel,
        impact
      })

      // Add impact message to chat
      this.addReadingLevelImpactToChat(language, oldLevel, newLevel, impact)

      return impact
    } catch (error) {
      console.error('Failed to update reading level with impact:', error)
      throw error
    }
  }

  private calculatePreferenceImpact(override: PreferenceOverride): PreferenceUpdateImpact[] {
    const impacts: PreferenceUpdateImpact[] = []
    
    if (override.type === 'topic') {
      const existingTopic = this.preferencesStore.topicPreferences.find(
        tp => tp.topic === override.key
      )
      
      const oldValue = existingTopic?.weight || 0
      const change = override.value - oldValue
      
      impacts.push({
        type: 'topic',
        item: override.key,
        oldValue,
        newValue: override.value,
        change,
        impactDescription: this.generateTopicImpactDescription(override.key, change),
        affectedRecommendations: this.estimateAffectedRecommendations(change)
      })
    } else if (override.type === 'content_type') {
      const existingType = this.preferencesStore.contentTypePreferences.find(
        ctp => ctp.type === override.key
      )
      
      const oldValue = existingType?.preference || 0
      const change = override.value - oldValue
      
      impacts.push({
        type: 'content_type',
        item: override.key,
        oldValue,
        newValue: override.value,
        change,
        impactDescription: this.generateContentTypeImpactDescription(override.key, change),
        affectedRecommendations: this.estimateAffectedRecommendations(change)
      })
    }

    return impacts
  }

  private calculateReadingLevelImpact(
    language: 'english' | 'japanese',
    oldLevel: number,
    newLevel: number
  ): PreferenceUpdateImpact[] {
    const change = newLevel - oldLevel
    
    return [{
      type: 'reading_level',
      item: language,
      oldValue: oldLevel,
      newValue: newLevel,
      change,
      impactDescription: this.generateReadingLevelImpactDescription(language, change),
      affectedRecommendations: this.estimateReadingLevelAffectedRecommendations(language, change)
    }]
  }

  private generateTopicImpactDescription(topic: string, change: number): string {
    const absChange = Math.abs(change)
    const direction = change > 0 ? 'increase' : 'decrease'
    const magnitude = absChange > 0.5 ? 'significantly' : absChange > 0.2 ? 'moderately' : 'slightly'
    
    return `This will ${magnitude} ${direction} recommendations for ${topic} content.`
  }

  private generateContentTypeImpactDescription(contentType: string, change: number): string {
    const absChange = Math.abs(change)
    const direction = change > 0 ? 'more' : 'fewer'
    const magnitude = absChange > 0.5 ? 'significantly' : absChange > 0.2 ? 'moderately' : 'slightly'
    
    return `You'll see ${magnitude} ${direction} ${contentType} recommendations.`
  }

  private generateReadingLevelImpactDescription(language: string, change: number): string {
    const direction = change > 0 ? 'more challenging' : 'easier'
    const magnitude = Math.abs(change) > 2 ? 'significantly' : Math.abs(change) > 1 ? 'moderately' : 'slightly'
    
    return `${language} recommendations will be ${magnitude} ${direction}.`
  }

  private estimateAffectedRecommendations(change: number): number {
    // Rough estimate based on change magnitude
    const absChange = Math.abs(change)
    if (absChange > 0.5) return Math.floor(Math.random() * 5) + 8 // 8-12 recommendations
    if (absChange > 0.2) return Math.floor(Math.random() * 3) + 4 // 4-6 recommendations
    return Math.floor(Math.random() * 2) + 1 // 1-2 recommendations
  }

  private estimateReadingLevelAffectedRecommendations(language: string, change: number): number {
    // Reading level changes typically affect more recommendations
    const absChange = Math.abs(change)
    if (absChange > 2) return Math.floor(Math.random() * 8) + 12 // 12-19 recommendations
    if (absChange > 1) return Math.floor(Math.random() * 5) + 6 // 6-10 recommendations
    return Math.floor(Math.random() * 3) + 2 // 2-4 recommendations
  }

  private addImpactMessageToChat(override: PreferenceOverride, impacts: PreferenceUpdateImpact[]) {
    const impact = impacts[0]
    if (!impact) return

    const message = `I've updated your ${override.type.replace('_', ' ')} preference for "${impact.item}". ${impact.impactDescription} This may affect about ${impact.affectedRecommendations} future recommendations.`
    
    this.chatStore.addNoahMessage(message, 'text', {
      preferenceUpdate: {
        type: override.type,
        item: impact.item,
        change: impact.change,
        impact: impact.impactDescription
      }
    })
  }

  private addReadingLevelImpactToChat(
    language: string,
    oldLevel: number,
    newLevel: number,
    impacts: PreferenceUpdateImpact[]
  ) {
    const impact = impacts[0]
    if (!impact) return

    const message = `I've updated your ${language} reading level from ${oldLevel.toFixed(1)} to ${newLevel.toFixed(1)}. ${impact.impactDescription} This will help me suggest more appropriate content for you.`
    
    this.chatStore.addNoahMessage(message, 'text', {
      readingLevelUpdate: {
        language,
        oldLevel,
        newLevel,
        impact: impact.impactDescription
      }
    })
  }

  private handlePreferenceUpdateNotification(data: { user_id: string, updated_preferences: any, timestamp: string }) {
    // Update local preferences store with real-time data
    if (data.updated_preferences) {
      this.preferencesStore.transparencyData = data.updated_preferences
      this.preferencesStore.lastUpdated = new Date(data.timestamp)
    }
  }

  private handleRecommendationRefresh(data: { user_id: string, new_recommendations: any[], timestamp: string }) {
    // Handle refreshed recommendations
    if (data.new_recommendations && data.new_recommendations.length > 0) {
      const message = `Based on your updated preferences, I've found ${data.new_recommendations.length} new recommendations that might interest you!`
      
      this.chatStore.addNoahMessage(message, 'recommendation', {
        recommendations: data.new_recommendations
      })
    }
  }

  // Public method to trigger recommendation refresh
  async refreshRecommendations(userId: string) {
    try {
      // Call API to get fresh recommendations based on updated preferences
      const response = await fetch(`/api/recommendations/${userId}?refresh=true`)
      if (!response.ok) throw new Error('Failed to refresh recommendations')
      
      const recommendations = await response.json()
      
      // Send via WebSocket for real-time delivery
      this.webSocket.sendPreferenceUpdate(userId, {
        type: 'recommendation_refresh',
        recommendations
      })
      
      return recommendations
    } catch (error) {
      console.error('Failed to refresh recommendations:', error)
      throw error
    }
  }
}

// Export singleton instance
export const preferenceUpdateService = new PreferenceUpdateService()