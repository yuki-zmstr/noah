export interface ChatMessage {
    id: string;
    content: string;
    sender: 'user' | 'noah';
    timestamp: Date;
    type: 'text' | 'recommendation' | 'purchase_links';
    metadata?: {
        recommendations?: BookRecommendation[];
        purchaseLinks?: PurchaseLink[];
    };
}
export interface BookRecommendation {
    id: string;
    title: string;
    author: string;
    description: string;
    coverUrl?: string;
    interestScore: number;
    readingLevel: string;
    estimatedReadingTime: number;
}
export interface PurchaseLink {
    id: string;
    type: 'amazon' | 'web_search' | 'library' | 'alternative_retailer';
    url: string;
    displayText: string;
    format?: 'physical' | 'digital' | 'audiobook';
    price?: string;
    availability: 'available' | 'pre_order' | 'out_of_stock' | 'unknown';
}
export interface TypingIndicator {
    isTyping: boolean;
    userId?: string;
}
export interface ChatSession {
    sessionId: string;
    userId: string;
    messages: ChatMessage[];
    isActive: boolean;
    lastActivity: Date;
}
