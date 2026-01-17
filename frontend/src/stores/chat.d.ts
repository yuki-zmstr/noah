import type { ChatMessage, ChatSession } from '@/types/chat';
export declare const useChatStore: import("pinia").StoreDefinition<"chat", Pick<{
    currentSession: import("vue").Ref<{
        sessionId: string;
        userId: string;
        messages: {
            id: string;
            content: string;
            sender: "user" | "noah";
            timestamp: Date;
            type: "text" | "recommendation" | "purchase_links";
            metadata?: {
                recommendations?: {
                    id: string;
                    title: string;
                    author: string;
                    description: string;
                    coverUrl?: string | undefined;
                    interestScore: number;
                    readingLevel: string;
                    estimatedReadingTime: number;
                }[] | undefined;
                purchaseLinks?: {
                    id: string;
                    type: "amazon" | "web_search" | "library" | "alternative_retailer";
                    url: string;
                    displayText: string;
                    format?: "physical" | "digital" | "audiobook" | undefined;
                    price?: string | undefined;
                    availability: "available" | "pre_order" | "out_of_stock" | "unknown";
                }[] | undefined;
            } | undefined;
        }[];
        isActive: boolean;
        lastActivity: Date;
    } | null, ChatSession | {
        sessionId: string;
        userId: string;
        messages: {
            id: string;
            content: string;
            sender: "user" | "noah";
            timestamp: Date;
            type: "text" | "recommendation" | "purchase_links";
            metadata?: {
                recommendations?: {
                    id: string;
                    title: string;
                    author: string;
                    description: string;
                    coverUrl?: string | undefined;
                    interestScore: number;
                    readingLevel: string;
                    estimatedReadingTime: number;
                }[] | undefined;
                purchaseLinks?: {
                    id: string;
                    type: "amazon" | "web_search" | "library" | "alternative_retailer";
                    url: string;
                    displayText: string;
                    format?: "physical" | "digital" | "audiobook" | undefined;
                    price?: string | undefined;
                    availability: "available" | "pre_order" | "out_of_stock" | "unknown";
                }[] | undefined;
            } | undefined;
        }[];
        isActive: boolean;
        lastActivity: Date;
    } | null>;
    messages: import("vue").Ref<{
        id: string;
        content: string;
        sender: "user" | "noah";
        timestamp: Date;
        type: "text" | "recommendation" | "purchase_links";
        metadata?: {
            recommendations?: {
                id: string;
                title: string;
                author: string;
                description: string;
                coverUrl?: string | undefined;
                interestScore: number;
                readingLevel: string;
                estimatedReadingTime: number;
            }[] | undefined;
            purchaseLinks?: {
                id: string;
                type: "amazon" | "web_search" | "library" | "alternative_retailer";
                url: string;
                displayText: string;
                format?: "physical" | "digital" | "audiobook" | undefined;
                price?: string | undefined;
                availability: "available" | "pre_order" | "out_of_stock" | "unknown";
            }[] | undefined;
        } | undefined;
    }[], ChatMessage[] | {
        id: string;
        content: string;
        sender: "user" | "noah";
        timestamp: Date;
        type: "text" | "recommendation" | "purchase_links";
        metadata?: {
            recommendations?: {
                id: string;
                title: string;
                author: string;
                description: string;
                coverUrl?: string | undefined;
                interestScore: number;
                readingLevel: string;
                estimatedReadingTime: number;
            }[] | undefined;
            purchaseLinks?: {
                id: string;
                type: "amazon" | "web_search" | "library" | "alternative_retailer";
                url: string;
                displayText: string;
                format?: "physical" | "digital" | "audiobook" | undefined;
                price?: string | undefined;
                availability: "available" | "pre_order" | "out_of_stock" | "unknown";
            }[] | undefined;
        } | undefined;
    }[]>;
    isLoading: import("vue").Ref<boolean, boolean>;
    error: import("vue").Ref<string | null, string | null>;
    sortedMessages: import("vue").ComputedRef<{
        id: string;
        content: string;
        sender: "user" | "noah";
        timestamp: Date;
        type: "text" | "recommendation" | "purchase_links";
        metadata?: {
            recommendations?: {
                id: string;
                title: string;
                author: string;
                description: string;
                coverUrl?: string | undefined;
                interestScore: number;
                readingLevel: string;
                estimatedReadingTime: number;
            }[] | undefined;
            purchaseLinks?: {
                id: string;
                type: "amazon" | "web_search" | "library" | "alternative_retailer";
                url: string;
                displayText: string;
                format?: "physical" | "digital" | "audiobook" | undefined;
                price?: string | undefined;
                availability: "available" | "pre_order" | "out_of_stock" | "unknown";
            }[] | undefined;
        } | undefined;
    }[]>;
    hasMessages: import("vue").ComputedRef<boolean>;
    initializeSession: (userId: string) => void;
    addMessage: (message: Omit<ChatMessage, "id" | "timestamp">) => ChatMessage;
    addUserMessage: (content: string) => ChatMessage;
    addNoahMessage: (content: string, type?: ChatMessage["type"], metadata?: ChatMessage["metadata"]) => ChatMessage;
    addStreamingMessage: (content: string, type?: ChatMessage["type"]) => ChatMessage;
    updateStreamingMessage: (messageId: string, content: string, metadata?: ChatMessage["metadata"], append?: boolean) => void;
    appendToStreamingMessage: (messageId: string, content: string, metadata?: ChatMessage["metadata"]) => void;
    finalizeStreamingMessage: (messageId: string, finalContent?: string, metadata?: ChatMessage["metadata"]) => void;
    clearMessages: () => void;
    setLoading: (loading: boolean) => void;
    setError: (errorMessage: string | null) => void;
    loadMessageHistory: (sessionId: string) => Promise<void>;
}, "messages" | "currentSession" | "isLoading" | "error">, Pick<{
    currentSession: import("vue").Ref<{
        sessionId: string;
        userId: string;
        messages: {
            id: string;
            content: string;
            sender: "user" | "noah";
            timestamp: Date;
            type: "text" | "recommendation" | "purchase_links";
            metadata?: {
                recommendations?: {
                    id: string;
                    title: string;
                    author: string;
                    description: string;
                    coverUrl?: string | undefined;
                    interestScore: number;
                    readingLevel: string;
                    estimatedReadingTime: number;
                }[] | undefined;
                purchaseLinks?: {
                    id: string;
                    type: "amazon" | "web_search" | "library" | "alternative_retailer";
                    url: string;
                    displayText: string;
                    format?: "physical" | "digital" | "audiobook" | undefined;
                    price?: string | undefined;
                    availability: "available" | "pre_order" | "out_of_stock" | "unknown";
                }[] | undefined;
            } | undefined;
        }[];
        isActive: boolean;
        lastActivity: Date;
    } | null, ChatSession | {
        sessionId: string;
        userId: string;
        messages: {
            id: string;
            content: string;
            sender: "user" | "noah";
            timestamp: Date;
            type: "text" | "recommendation" | "purchase_links";
            metadata?: {
                recommendations?: {
                    id: string;
                    title: string;
                    author: string;
                    description: string;
                    coverUrl?: string | undefined;
                    interestScore: number;
                    readingLevel: string;
                    estimatedReadingTime: number;
                }[] | undefined;
                purchaseLinks?: {
                    id: string;
                    type: "amazon" | "web_search" | "library" | "alternative_retailer";
                    url: string;
                    displayText: string;
                    format?: "physical" | "digital" | "audiobook" | undefined;
                    price?: string | undefined;
                    availability: "available" | "pre_order" | "out_of_stock" | "unknown";
                }[] | undefined;
            } | undefined;
        }[];
        isActive: boolean;
        lastActivity: Date;
    } | null>;
    messages: import("vue").Ref<{
        id: string;
        content: string;
        sender: "user" | "noah";
        timestamp: Date;
        type: "text" | "recommendation" | "purchase_links";
        metadata?: {
            recommendations?: {
                id: string;
                title: string;
                author: string;
                description: string;
                coverUrl?: string | undefined;
                interestScore: number;
                readingLevel: string;
                estimatedReadingTime: number;
            }[] | undefined;
            purchaseLinks?: {
                id: string;
                type: "amazon" | "web_search" | "library" | "alternative_retailer";
                url: string;
                displayText: string;
                format?: "physical" | "digital" | "audiobook" | undefined;
                price?: string | undefined;
                availability: "available" | "pre_order" | "out_of_stock" | "unknown";
            }[] | undefined;
        } | undefined;
    }[], ChatMessage[] | {
        id: string;
        content: string;
        sender: "user" | "noah";
        timestamp: Date;
        type: "text" | "recommendation" | "purchase_links";
        metadata?: {
            recommendations?: {
                id: string;
                title: string;
                author: string;
                description: string;
                coverUrl?: string | undefined;
                interestScore: number;
                readingLevel: string;
                estimatedReadingTime: number;
            }[] | undefined;
            purchaseLinks?: {
                id: string;
                type: "amazon" | "web_search" | "library" | "alternative_retailer";
                url: string;
                displayText: string;
                format?: "physical" | "digital" | "audiobook" | undefined;
                price?: string | undefined;
                availability: "available" | "pre_order" | "out_of_stock" | "unknown";
            }[] | undefined;
        } | undefined;
    }[]>;
    isLoading: import("vue").Ref<boolean, boolean>;
    error: import("vue").Ref<string | null, string | null>;
    sortedMessages: import("vue").ComputedRef<{
        id: string;
        content: string;
        sender: "user" | "noah";
        timestamp: Date;
        type: "text" | "recommendation" | "purchase_links";
        metadata?: {
            recommendations?: {
                id: string;
                title: string;
                author: string;
                description: string;
                coverUrl?: string | undefined;
                interestScore: number;
                readingLevel: string;
                estimatedReadingTime: number;
            }[] | undefined;
            purchaseLinks?: {
                id: string;
                type: "amazon" | "web_search" | "library" | "alternative_retailer";
                url: string;
                displayText: string;
                format?: "physical" | "digital" | "audiobook" | undefined;
                price?: string | undefined;
                availability: "available" | "pre_order" | "out_of_stock" | "unknown";
            }[] | undefined;
        } | undefined;
    }[]>;
    hasMessages: import("vue").ComputedRef<boolean>;
    initializeSession: (userId: string) => void;
    addMessage: (message: Omit<ChatMessage, "id" | "timestamp">) => ChatMessage;
    addUserMessage: (content: string) => ChatMessage;
    addNoahMessage: (content: string, type?: ChatMessage["type"], metadata?: ChatMessage["metadata"]) => ChatMessage;
    addStreamingMessage: (content: string, type?: ChatMessage["type"]) => ChatMessage;
    updateStreamingMessage: (messageId: string, content: string, metadata?: ChatMessage["metadata"], append?: boolean) => void;
    appendToStreamingMessage: (messageId: string, content: string, metadata?: ChatMessage["metadata"]) => void;
    finalizeStreamingMessage: (messageId: string, finalContent?: string, metadata?: ChatMessage["metadata"]) => void;
    clearMessages: () => void;
    setLoading: (loading: boolean) => void;
    setError: (errorMessage: string | null) => void;
    loadMessageHistory: (sessionId: string) => Promise<void>;
}, "sortedMessages" | "hasMessages">, Pick<{
    currentSession: import("vue").Ref<{
        sessionId: string;
        userId: string;
        messages: {
            id: string;
            content: string;
            sender: "user" | "noah";
            timestamp: Date;
            type: "text" | "recommendation" | "purchase_links";
            metadata?: {
                recommendations?: {
                    id: string;
                    title: string;
                    author: string;
                    description: string;
                    coverUrl?: string | undefined;
                    interestScore: number;
                    readingLevel: string;
                    estimatedReadingTime: number;
                }[] | undefined;
                purchaseLinks?: {
                    id: string;
                    type: "amazon" | "web_search" | "library" | "alternative_retailer";
                    url: string;
                    displayText: string;
                    format?: "physical" | "digital" | "audiobook" | undefined;
                    price?: string | undefined;
                    availability: "available" | "pre_order" | "out_of_stock" | "unknown";
                }[] | undefined;
            } | undefined;
        }[];
        isActive: boolean;
        lastActivity: Date;
    } | null, ChatSession | {
        sessionId: string;
        userId: string;
        messages: {
            id: string;
            content: string;
            sender: "user" | "noah";
            timestamp: Date;
            type: "text" | "recommendation" | "purchase_links";
            metadata?: {
                recommendations?: {
                    id: string;
                    title: string;
                    author: string;
                    description: string;
                    coverUrl?: string | undefined;
                    interestScore: number;
                    readingLevel: string;
                    estimatedReadingTime: number;
                }[] | undefined;
                purchaseLinks?: {
                    id: string;
                    type: "amazon" | "web_search" | "library" | "alternative_retailer";
                    url: string;
                    displayText: string;
                    format?: "physical" | "digital" | "audiobook" | undefined;
                    price?: string | undefined;
                    availability: "available" | "pre_order" | "out_of_stock" | "unknown";
                }[] | undefined;
            } | undefined;
        }[];
        isActive: boolean;
        lastActivity: Date;
    } | null>;
    messages: import("vue").Ref<{
        id: string;
        content: string;
        sender: "user" | "noah";
        timestamp: Date;
        type: "text" | "recommendation" | "purchase_links";
        metadata?: {
            recommendations?: {
                id: string;
                title: string;
                author: string;
                description: string;
                coverUrl?: string | undefined;
                interestScore: number;
                readingLevel: string;
                estimatedReadingTime: number;
            }[] | undefined;
            purchaseLinks?: {
                id: string;
                type: "amazon" | "web_search" | "library" | "alternative_retailer";
                url: string;
                displayText: string;
                format?: "physical" | "digital" | "audiobook" | undefined;
                price?: string | undefined;
                availability: "available" | "pre_order" | "out_of_stock" | "unknown";
            }[] | undefined;
        } | undefined;
    }[], ChatMessage[] | {
        id: string;
        content: string;
        sender: "user" | "noah";
        timestamp: Date;
        type: "text" | "recommendation" | "purchase_links";
        metadata?: {
            recommendations?: {
                id: string;
                title: string;
                author: string;
                description: string;
                coverUrl?: string | undefined;
                interestScore: number;
                readingLevel: string;
                estimatedReadingTime: number;
            }[] | undefined;
            purchaseLinks?: {
                id: string;
                type: "amazon" | "web_search" | "library" | "alternative_retailer";
                url: string;
                displayText: string;
                format?: "physical" | "digital" | "audiobook" | undefined;
                price?: string | undefined;
                availability: "available" | "pre_order" | "out_of_stock" | "unknown";
            }[] | undefined;
        } | undefined;
    }[]>;
    isLoading: import("vue").Ref<boolean, boolean>;
    error: import("vue").Ref<string | null, string | null>;
    sortedMessages: import("vue").ComputedRef<{
        id: string;
        content: string;
        sender: "user" | "noah";
        timestamp: Date;
        type: "text" | "recommendation" | "purchase_links";
        metadata?: {
            recommendations?: {
                id: string;
                title: string;
                author: string;
                description: string;
                coverUrl?: string | undefined;
                interestScore: number;
                readingLevel: string;
                estimatedReadingTime: number;
            }[] | undefined;
            purchaseLinks?: {
                id: string;
                type: "amazon" | "web_search" | "library" | "alternative_retailer";
                url: string;
                displayText: string;
                format?: "physical" | "digital" | "audiobook" | undefined;
                price?: string | undefined;
                availability: "available" | "pre_order" | "out_of_stock" | "unknown";
            }[] | undefined;
        } | undefined;
    }[]>;
    hasMessages: import("vue").ComputedRef<boolean>;
    initializeSession: (userId: string) => void;
    addMessage: (message: Omit<ChatMessage, "id" | "timestamp">) => ChatMessage;
    addUserMessage: (content: string) => ChatMessage;
    addNoahMessage: (content: string, type?: ChatMessage["type"], metadata?: ChatMessage["metadata"]) => ChatMessage;
    addStreamingMessage: (content: string, type?: ChatMessage["type"]) => ChatMessage;
    updateStreamingMessage: (messageId: string, content: string, metadata?: ChatMessage["metadata"], append?: boolean) => void;
    appendToStreamingMessage: (messageId: string, content: string, metadata?: ChatMessage["metadata"]) => void;
    finalizeStreamingMessage: (messageId: string, finalContent?: string, metadata?: ChatMessage["metadata"]) => void;
    clearMessages: () => void;
    setLoading: (loading: boolean) => void;
    setError: (errorMessage: string | null) => void;
    loadMessageHistory: (sessionId: string) => Promise<void>;
}, "initializeSession" | "addMessage" | "addUserMessage" | "addNoahMessage" | "addStreamingMessage" | "updateStreamingMessage" | "appendToStreamingMessage" | "finalizeStreamingMessage" | "clearMessages" | "setLoading" | "setError" | "loadMessageHistory">>;
