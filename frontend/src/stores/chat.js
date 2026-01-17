import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
export const useChatStore = defineStore('chat', () => {
    // State
    const currentSession = ref(null);
    const messages = ref([]);
    const isLoading = ref(false);
    const error = ref(null);
    // Getters
    const sortedMessages = computed(() => {
        return [...messages.value].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    });
    const hasMessages = computed(() => messages.value.length > 0);
    // Actions
    const initializeSession = (userId) => {
        const sessionId = `session_${userId}_${Date.now()}`;
        currentSession.value = {
            sessionId,
            userId,
            messages: [],
            isActive: true,
            lastActivity: new Date()
        };
        messages.value = [];
        error.value = null;
    };
    const addMessage = (message) => {
        const newMessage = {
            ...message,
            id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            timestamp: new Date()
        };
        messages.value.push(newMessage);
        if (currentSession.value) {
            currentSession.value.lastActivity = new Date();
            currentSession.value.messages.push(newMessage);
        }
        return newMessage;
    };
    const addUserMessage = (content) => {
        return addMessage({
            content,
            sender: 'user',
            type: 'text'
        });
    };
    const addNoahMessage = (content, type = 'text', metadata) => {
        return addMessage({
            content,
            sender: 'noah',
            type,
            metadata
        });
    };
    const addStreamingMessage = (content, type = 'text') => {
        const newMessage = {
            id: `msg_streaming_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            content,
            sender: 'noah',
            type,
            timestamp: new Date()
        };
        messages.value.push(newMessage);
        if (currentSession.value) {
            currentSession.value.lastActivity = new Date();
            currentSession.value.messages.push(newMessage);
        }
        return newMessage;
    };
    const updateStreamingMessage = (messageId, content, metadata, append = false) => {
        const messageIndex = messages.value.findIndex(msg => msg.id === messageId);
        if (messageIndex !== -1) {
            if (append) {
                // Append new content to existing content
                messages.value[messageIndex].content += content;
            }
            else {
                // Replace content (for backward compatibility)
                messages.value[messageIndex].content = content;
            }
            if (metadata) {
                messages.value[messageIndex].metadata = metadata;
            }
            // Update in session as well
            if (currentSession.value) {
                const sessionMessageIndex = currentSession.value.messages.findIndex(msg => msg.id === messageId);
                if (sessionMessageIndex !== -1) {
                    if (append) {
                        currentSession.value.messages[sessionMessageIndex].content += content;
                    }
                    else {
                        currentSession.value.messages[sessionMessageIndex].content = content;
                    }
                    if (metadata) {
                        currentSession.value.messages[sessionMessageIndex].metadata = metadata;
                    }
                }
            }
        }
    };
    const appendToStreamingMessage = (messageId, content, metadata) => {
        updateStreamingMessage(messageId, content, metadata, true);
    };
    const finalizeStreamingMessage = (messageId, finalContent, metadata) => {
        // If finalContent is provided, replace the entire content (for cases where backend sends complete message)
        // Otherwise, just mark as finalized (content was already accumulated via chunks)
        if (finalContent) {
            updateStreamingMessage(messageId, finalContent, metadata, false);
        }
        else if (metadata) {
            updateStreamingMessage(messageId, '', metadata, false);
        }
    };
    const clearMessages = () => {
        messages.value = [];
        if (currentSession.value) {
            currentSession.value.messages = [];
        }
    };
    const setLoading = (loading) => {
        isLoading.value = loading;
    };
    const setError = (errorMessage) => {
        error.value = errorMessage;
    };
    const loadMessageHistory = async (sessionId) => {
        try {
            setLoading(true);
            setError(null);
            // TODO: Implement API call to load message history
            // For now, we'll just clear messages as if starting fresh
            clearMessages();
        }
        catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load message history');
        }
        finally {
            setLoading(false);
        }
    };
    return {
        // State
        currentSession,
        messages,
        isLoading,
        error,
        // Getters
        sortedMessages,
        hasMessages,
        // Actions
        initializeSession,
        addMessage,
        addUserMessage,
        addNoahMessage,
        addStreamingMessage,
        updateStreamingMessage,
        appendToStreamingMessage,
        finalizeStreamingMessage,
        clearMessages,
        setLoading,
        setError,
        loadMessageHistory
    };
});
