// Core type definitions for Noah Reading Agent

export interface UserProfile {
  id: string
  userId: string
  preferences: PreferenceModel
  readingLevels: LanguageReadingLevels
  behaviorHistory: ReadingBehavior[]
  lastUpdated: Date
}

export interface PreferenceModel {
  topics: TopicPreference[]
  contentTypes: ContentTypePreference[]
  contextualPreferences: ContextualPreference[]
  evolutionHistory: PreferenceSnapshot[]
}

export interface LanguageReadingLevels {
  english: ReadingLevel
  japanese: ReadingLevel
}

export interface ReadingLevel {
  level: 'beginner' | 'intermediate' | 'advanced'
  confidence: number
  lastAssessed: Date
}

export interface TopicPreference {
  topic: string
  weight: number
  confidence: number
  lastUpdated: Date
  evolutionTrend: 'increasing' | 'decreasing' | 'stable'
}

export interface ContentTypePreference {
  type: 'fiction' | 'non-fiction' | 'technical' | 'academic' | 'news'
  preference: number
  lastUpdated: Date
}

export interface ContextualPreference {
  context: string
  preference: number
  conditions: Record<string, any>
}

export interface PreferenceSnapshot {
  timestamp: Date
  topicWeights: Map<string, number>
  readingLevelPreference: number
  contextualFactors: Map<string, number>
  confidenceScore: number
}

export interface ContentItem {
  id: string
  title: string
  content: string
  language: 'english' | 'japanese'
  metadata: ContentMetadata
  analysis: ContentAnalysis
  adaptations: ContentAdaptation[]
}

export interface ContentMetadata {
  author: string
  source: string
  publishDate: Date
  contentType: ContentType
  estimatedReadingTime: number
  tags: string[]
}

export interface ContentAnalysis {
  topics: TopicScore[]
  readingLevel: ReadingLevelScore
  complexity: ComplexityMetrics
  embedding: number[]
  keyPhrases: string[]
}

export interface ContentAdaptation {
  targetLevel: ReadingLevel
  adaptedContent: string
  adaptationMethod: string
  preservationScore: number
}

export interface ReadingBehavior {
  contentId: string
  sessionId: string
  startTime: Date
  endTime: Date
  completionRate: number
  readingSpeed: number
  pausePatterns: PauseEvent[]
  interactions: InteractionEvent[]
  context: ReadingContext
}

export interface ReadingContext {
  timeOfDay: string
  deviceType: string
  location?: string
  availableTime?: number
  userMood?: string
}

export interface ConversationSession {
  sessionId: string
  userId: string
  messages: ConversationMessage[]
  context: ConversationContext
  startTime: Date
  lastActivity: Date
  isPersistent: boolean
}

export interface ConversationMessage {
  messageId: string
  sender: 'user' | 'noah'
  content: string
  timestamp: Date
  intent?: UserIntent
  recommendations?: ContentRecommendation[]
  purchaseLinks?: PurchaseLink[]
}

export interface ConversationContext {
  currentTopic?: string
  recentRecommendations: string[]
  userMood?: string
  discoveryModeActive: boolean
  preferredLanguage: 'english' | 'japanese'
}

export interface PurchaseLink {
  linkId: string
  contentId: string
  linkType: 'amazon' | 'web_search' | 'library' | 'alternative_retailer'
  url: string
  displayText: string
  format?: 'physical' | 'digital' | 'audiobook'
  price?: string
  availability: 'available' | 'pre_order' | 'out_of_stock' | 'unknown'
  generatedAt: Date
}

export interface DiscoveryRecommendation {
  contentId: string
  divergenceScore: number
  bridgingTopics: string[]
  discoveryReason: string
  userResponse?: 'interested' | 'not_interested' | 'purchased' | 'saved'
  responseTimestamp?: Date
}

// Supporting types
export type ContentType = 'article' | 'book' | 'paper' | 'blog_post' | 'news'
export type UserIntent = 'recommendation' | 'question' | 'feedback' | 'discovery' | 'purchase'

export interface TopicScore {
  topic: string
  score: number
  confidence: number
}

export interface ReadingLevelScore {
  level: number
  confidence: number
  metrics: Record<string, number>
}

export interface ComplexityMetrics {
  vocabularyComplexity: number
  syntacticComplexity: number
  semanticComplexity: number
  overallComplexity: number
}

export interface PauseEvent {
  timestamp: Date
  duration: number
  location: number
}

export interface InteractionEvent {
  type: 'highlight' | 'note' | 'bookmark' | 'share'
  timestamp: Date
  location: number
  data?: any
}

export interface ContentRecommendation {
  contentId: string
  title: string
  reason: string
  confidence: number
  purchaseLinks?: PurchaseLink[]
}