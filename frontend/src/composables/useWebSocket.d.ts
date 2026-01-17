import type { ChatMessage, TypingIndicator } from '@/types/chat';
export declare function useWebSocket(serverUrl?: string): {
    socket: import("vue").Ref<{
        binaryType: BinaryType;
        readonly bufferedAmount: number;
        readonly extensions: string;
        onclose: ((this: WebSocket, ev: CloseEvent) => any) | null;
        onerror: ((this: WebSocket, ev: Event) => any) | null;
        onmessage: ((this: WebSocket, ev: MessageEvent) => any) | null;
        onopen: ((this: WebSocket, ev: Event) => any) | null;
        readonly protocol: string;
        readonly readyState: number;
        readonly url: string;
        close: (code?: number, reason?: string) => void;
        send: (data: string | ArrayBufferLike | Blob | ArrayBufferView) => void;
        readonly CONNECTING: 0;
        readonly OPEN: 1;
        readonly CLOSING: 2;
        readonly CLOSED: 3;
        addEventListener: {
            <K extends keyof WebSocketEventMap>(type: K, listener: (this: WebSocket, ev: WebSocketEventMap[K]) => any, options?: boolean | AddEventListenerOptions): void;
            (type: string, listener: EventListenerOrEventListenerObject, options?: boolean | AddEventListenerOptions): void;
        };
        removeEventListener: {
            <K extends keyof WebSocketEventMap>(type: K, listener: (this: WebSocket, ev: WebSocketEventMap[K]) => any, options?: boolean | EventListenerOptions): void;
            (type: string, listener: EventListenerOrEventListenerObject, options?: boolean | EventListenerOptions): void;
        };
        dispatchEvent: (event: Event) => boolean;
    } | null, WebSocket | {
        binaryType: BinaryType;
        readonly bufferedAmount: number;
        readonly extensions: string;
        onclose: ((this: WebSocket, ev: CloseEvent) => any) | null;
        onerror: ((this: WebSocket, ev: Event) => any) | null;
        onmessage: ((this: WebSocket, ev: MessageEvent) => any) | null;
        onopen: ((this: WebSocket, ev: Event) => any) | null;
        readonly protocol: string;
        readonly readyState: number;
        readonly url: string;
        close: (code?: number, reason?: string) => void;
        send: (data: string | ArrayBufferLike | Blob | ArrayBufferView) => void;
        readonly CONNECTING: 0;
        readonly OPEN: 1;
        readonly CLOSING: 2;
        readonly CLOSED: 3;
        addEventListener: {
            <K extends keyof WebSocketEventMap>(type: K, listener: (this: WebSocket, ev: WebSocketEventMap[K]) => any, options?: boolean | AddEventListenerOptions): void;
            (type: string, listener: EventListenerOrEventListenerObject, options?: boolean | AddEventListenerOptions): void;
        };
        removeEventListener: {
            <K extends keyof WebSocketEventMap>(type: K, listener: (this: WebSocket, ev: WebSocketEventMap[K]) => any, options?: boolean | EventListenerOptions): void;
            (type: string, listener: EventListenerOrEventListenerObject, options?: boolean | EventListenerOptions): void;
        };
        dispatchEvent: (event: Event) => boolean;
    } | null>;
    isConnected: import("vue").Ref<boolean, boolean>;
    connectionError: import("vue").Ref<string | null, string | null>;
    connect: () => void;
    disconnect: () => void;
    sendMessage: (message: string, sessionId: string, metadata?: any) => void;
    onMessage: (callback: (message: ChatMessage) => void) => void;
    onMessageChunk: (callback: (chunk: {
        content: string;
        is_final: boolean;
        timestamp: string;
    }) => void) => void;
    onRecommendations: (callback: (data: {
        recommendations: any[];
        is_discovery?: boolean;
        timestamp: string;
    }) => void) => void;
    onPurchaseLinks: (callback: (data: {
        purchase_links: any[];
        timestamp: string;
    }) => void) => void;
    onMessageComplete: (callback: (data: {
        message_id: string;
        timestamp: string;
    }) => void) => void;
    onTyping: (callback: (typing: TypingIndicator) => void) => void;
    onConversationHistory: (callback: (data: {
        messages: ChatMessage[];
    }) => void) => void;
    joinSession: (sessionId: string, userId: string) => void;
};
