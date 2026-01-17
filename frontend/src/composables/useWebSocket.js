import { ref, onMounted, onUnmounted } from 'vue';
export function useWebSocket(serverUrl = 'ws://localhost:8000') {
    const socket = ref(null);
    const isConnected = ref(false);
    const connectionError = ref(null);
    const connectionId = ref(`conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
    const connect = () => {
        try {
            const wsUrl = `${serverUrl}/api/v1/chat/ws/${connectionId.value}`;
            socket.value = new WebSocket(wsUrl);
            socket.value.onopen = () => {
                isConnected.value = true;
                connectionError.value = null;
                console.log('WebSocket connected');
            };
            socket.value.onclose = () => {
                isConnected.value = false;
                console.log('WebSocket disconnected');
            };
            socket.value.onerror = (error) => {
                connectionError.value = 'WebSocket connection error';
                console.error('WebSocket connection error:', error);
            };
            socket.value.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                }
                catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
        }
        catch (error) {
            connectionError.value = error instanceof Error ? error.message : 'Unknown connection error';
        }
    };
    const disconnect = () => {
        if (socket.value) {
            socket.value.close();
            socket.value = null;
            isConnected.value = false;
        }
    };
    // Message handlers
    const messageHandlers = {
        noah_message: [],
        noah_message_chunk: [],
        noah_recommendations: [],
        noah_purchase_links: [],
        noah_message_complete: [],
        typing: [],
        conversation_history: [],
    };
    const handleMessage = (data) => {
        const { type } = data;
        if (messageHandlers[type]) {
            messageHandlers[type].forEach((handler) => handler(data));
        }
    };
    const sendMessage = (message, sessionId, metadata) => {
        if (socket.value && isConnected.value) {
            const payload = {
                type: 'user_message',
                content: message,
                sessionId,
                timestamp: new Date().toISOString(),
                metadata
            };
            socket.value.send(JSON.stringify(payload));
        }
    };
    const onMessage = (callback) => {
        messageHandlers.noah_message.push(callback);
    };
    const onMessageChunk = (callback) => {
        messageHandlers.noah_message_chunk.push(callback);
    };
    const onRecommendations = (callback) => {
        messageHandlers.noah_recommendations.push(callback);
    };
    const onPurchaseLinks = (callback) => {
        messageHandlers.noah_purchase_links.push(callback);
    };
    const onMessageComplete = (callback) => {
        messageHandlers.noah_message_complete.push(callback);
    };
    const onTyping = (callback) => {
        messageHandlers.typing.push(callback);
    };
    const onConversationHistory = (callback) => {
        messageHandlers.conversation_history.push(callback);
    };
    const joinSession = (sessionId, userId) => {
        if (socket.value && isConnected.value) {
            const payload = {
                type: 'join_session',
                sessionId,
                userId
            };
            socket.value.send(JSON.stringify(payload));
        }
    };
    onMounted(() => {
        connect();
    });
    onUnmounted(() => {
        disconnect();
    });
    return {
        socket,
        isConnected,
        connectionError,
        connect,
        disconnect,
        sendMessage,
        onMessage,
        onMessageChunk,
        onRecommendations,
        onPurchaseLinks,
        onMessageComplete,
        onTyping,
        onConversationHistory,
        joinSession
    };
}
