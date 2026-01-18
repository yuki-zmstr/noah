export interface TopicPreference {
  topic: string
  weight: number
  confidence: number
  last_updated: string
  evolution_trend: 'increasing' | 'decreasing' | 'stable' | 'new' | 'manual_override'
  explanation?: string
  related_sessions?: number
}

export interface ContentTypePreference {
  type: string
  preference: number
  last_updated: string
  explanation?: string
  sessions_count?: number
}

export interface ContextualPreference {
  factor: string
  value: string
  weight: number
  last_updated: string
  explanation?: string
  sessions_count?: number
}

export interface ReadingLevel {
  level: number
  confidence: number
  assessment_count: number
  last_assessment?: string
  explanation?: string
}

export interface LanguageReadingLevels {
  english: ReadingLevel
  japanese: ReadingLevel
}

export interface PreferenceModel {
  topics: TopicPreference[]
  content_types: ContentTypePreference[]
  contextual_preferences: ContextualPreference[]
  evolution_history: any[]
}

export interface PreferenceTransparency {
  user_id: string
  profile_created: string
  last_updated: string
  data_points_analyzed: number
  reading_levels: LanguageReadingLevels
  topic_preferences: TopicPreference[]
  content_type_preferences: ContentTypePreference[]
  contextual_patterns: ContextualPreference[]
  preference_evolution: {
    has_evolution: boolean
    explanation: string
    recent_changes_count?: number
    recent_changes?: any[]
  }
}

export interface PreferenceOverride {
  type: 'topic' | 'content_type' | 'contextual'
  key: string
  value: number
  factor?: string
  context_value?: string
}

export interface PreferenceEvolution {
  evolution_detected: boolean
  trends: Array<{
    type: string
    item: string
    change: number
    direction: 'increasing' | 'decreasing'
    magnitude: number
  }>
  analysis_period?: {
    start: string
    end: string
    snapshots_analyzed: number
  }
}