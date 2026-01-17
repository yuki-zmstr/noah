import { ref, onMounted, nextTick, watch } from "vue";
import { RouterLink } from "vue-router";
import { useChatStore } from "@/stores/chat";
import { useLanguageStore } from "@/stores/language";
import { useWebSocket } from "@/composables/useWebSocket";
import ChatMessage from "@/components/ChatMessage.vue";
import TypingIndicator from "@/components/TypingIndicator.vue";
import LanguageToggle from "@/components/LanguageToggle.vue";
const { defineProps, defineSlots, defineEmits, defineExpose, defineModel, defineOptions, withDefaults, } = await import('vue');
// Store and composables
const chatStore = useChatStore();
const languageStore = useLanguageStore();
const { isConnected, connectionError, sendMessage: sendWebSocketMessage, onMessage, onMessageChunk, onRecommendations, onPurchaseLinks, onMessageComplete, onTyping, onConversationHistory, joinSession, } = useWebSocket();
// Reactive state
const messageInput = ref("");
const messagesContainer = ref();
const isTyping = ref(false);
const typingTimeout = ref();
const currentStreamingMessage = ref(null);
// Computed properties from store - use store directly for reactivity
// Mock user ID for development
const userId = "user_" + Math.random().toString(36).substr(2, 9);
// Methods
const sendMessage = async () => {
    const message = messageInput.value.trim();
    if (!message || !isConnected.value)
        return;
    // Add user message to store
    chatStore.addUserMessage(message);
    messageInput.value = "";
    // Send via WebSocket
    if (chatStore.currentSession) {
        sendWebSocketMessage(message, chatStore.currentSession.sessionId, {
            language: languageStore.currentLanguage,
        });
    }
    // Scroll to bottom
    await nextTick();
    scrollToBottom();
    // Simulate Noah's response for development (remove when backend is ready)
    simulateNoahResponse(message);
};
const simulateNoahResponse = (userMessage) => {
    // Show typing indicator
    isTyping.value = true;
    setTimeout(() => {
        isTyping.value = false;
        // Generate mock response based on user message - match backend responses
        let response = "I'm Noah, your reading companion. How can I help you discover your next great read?";
        let messageType = "text";
        let metadata = undefined;
        if (userMessage.toLowerCase().includes("recommend") ||
            userMessage.toLowerCase().includes("book")) {
            response =
                "I'd be happy to recommend some books for you! What genres or topics interest you?";
            messageType = "recommendation";
            metadata = {
                recommendations: [
                    {
                        id: "book_1",
                        title: "The Seven Husbands of Evelyn Hugo",
                        author: "Taylor Jenkins Reid",
                        description: "A captivating novel about a reclusive Hollywood icon who finally decides to tell her story.",
                        interestScore: 0.92,
                        readingLevel: "Intermediate",
                        estimatedReadingTime: 420,
                    },
                    {
                        id: "book_2",
                        title: "Educated",
                        author: "Tara Westover",
                        description: "A powerful memoir about education, family, and the struggle between loyalty and independence.",
                        interestScore: 0.88,
                        readingLevel: "Advanced",
                        estimatedReadingTime: 380,
                    },
                ],
            };
        }
        else if (userMessage.toLowerCase().includes("lucky") ||
            userMessage.toLowerCase().includes("discover")) {
            response =
                "Let's explore something new! I'll find some books outside your usual preferences.";
            messageType = "recommendation";
            metadata = {
                recommendations: [
                    {
                        id: "book_discovery",
                        title: "Klara and the Sun",
                        author: "Kazuo Ishiguro",
                        description: "A thought-provoking story told from the perspective of an artificial friend.",
                        interestScore: 0.75,
                        readingLevel: "Intermediate",
                        estimatedReadingTime: 300,
                    },
                ],
            };
        }
        else if (userMessage.toLowerCase().includes("buy") ||
            userMessage.toLowerCase().includes("purchase")) {
            response =
                "I can help you find where to buy that book. Let me generate some purchase links for you.";
            messageType = "purchase_links";
            metadata = {
                purchaseLinks: [
                    {
                        id: "amazon_link",
                        type: "amazon",
                        url: "https://amazon.com/example",
                        displayText: "Buy on Amazon",
                        format: "physical",
                        price: "$14.99",
                        availability: "available",
                    },
                    {
                        id: "search_link",
                        type: "web_search",
                        url: "https://google.com/search?q=book+title",
                        displayText: "Search for more options",
                        availability: "unknown",
                    },
                ],
            };
        }
        chatStore.addNoahMessage(response, messageType, metadata);
        // Scroll to bottom after adding message
        nextTick(() => scrollToBottom());
    }, 1500 + Math.random() * 1000); // Random delay between 1.5-2.5 seconds
};
const scrollToBottom = () => {
    if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
};
const clearError = () => {
    chatStore.setError(null);
};
// WebSocket event handlers
onMessage((message) => {
    chatStore.addMessage(message);
    nextTick(() => scrollToBottom());
});
// Handle streaming message chunks
onMessageChunk((chunk) => {
    if (!currentStreamingMessage.value) {
        // Start a new streaming message with the first chunk
        currentStreamingMessage.value = chatStore.addStreamingMessage(chunk.content);
    }
    else {
        // Append new chunk to existing streaming message with a space separator
        chatStore.appendToStreamingMessage(currentStreamingMessage.value.id, " " + chunk.content);
    }
    nextTick(() => scrollToBottom());
});
// Handle recommendations
onRecommendations((data) => {
    if (currentStreamingMessage.value) {
        const messageType = data.is_discovery ? "recommendation" : "recommendation";
        chatStore.updateStreamingMessage(currentStreamingMessage.value.id, currentStreamingMessage.value.content, { recommendations: data.recommendations });
        // Update message type
        const messageIndex = chatStore.messages.findIndex((msg) => msg.id === currentStreamingMessage.value?.id);
        if (messageIndex !== -1) {
            chatStore.messages[messageIndex].type = messageType;
        }
    }
    nextTick(() => scrollToBottom());
});
// Handle purchase links
onPurchaseLinks((data) => {
    if (currentStreamingMessage.value) {
        chatStore.updateStreamingMessage(currentStreamingMessage.value.id, currentStreamingMessage.value.content, { purchaseLinks: data.purchase_links });
        // Update message type
        const messageIndex = chatStore.messages.findIndex((msg) => msg.id === currentStreamingMessage.value?.id);
        if (messageIndex !== -1) {
            chatStore.messages[messageIndex].type = "purchase_links";
        }
    }
    nextTick(() => scrollToBottom());
});
// Handle message completion
onMessageComplete((data) => {
    if (currentStreamingMessage.value) {
        // Finalize the streaming message (content is already accumulated from chunks)
        chatStore.finalizeStreamingMessage(currentStreamingMessage.value.id);
        currentStreamingMessage.value = null;
    }
    nextTick(() => scrollToBottom());
});
// Handle conversation history
onConversationHistory((data) => {
    // Load historical messages
    data.messages.forEach((msg) => {
        chatStore.addMessage({
            id: msg.message_id || `msg_${Date.now()}_${Math.random()}`,
            content: msg.content,
            sender: msg.sender,
            timestamp: new Date(msg.timestamp),
            type: msg.type || "text",
            metadata: msg.metadata,
        });
    });
    nextTick(() => scrollToBottom());
});
onTyping((typing) => {
    isTyping.value = typing.isTyping;
    if (typing.isTyping) {
        // Clear existing timeout
        if (typingTimeout.value) {
            clearTimeout(typingTimeout.value);
        }
        // Set timeout to hide typing indicator
        typingTimeout.value = setTimeout(() => {
            isTyping.value = false;
        }, 5000);
    }
});
// Watch for connection errors
watch(connectionError, (error) => {
    if (error) {
        chatStore.setError(`Connection error: ${error}`);
    }
});
// Initialize on mount
onMounted(() => {
    languageStore.initializeLanguage();
    chatStore.initializeSession(userId);
    // Join WebSocket session when connected
    watch(isConnected, (connected) => {
        if (connected && chatStore.currentSession) {
            joinSession(chatStore.currentSession.sessionId, userId);
        }
    }, { immediate: true });
});
const __VLS_fnComponent = (await import('vue')).defineComponent({});
;
let __VLS_functionalComponentProps;
function __VLS_template() {
    const __VLS_ctx = {};
    const __VLS_localComponents = {
        ...{},
        ...{},
        ...__VLS_ctx,
    };
    let __VLS_components;
    const __VLS_localDirectives = {
        ...{},
        ...__VLS_ctx,
    };
    let __VLS_directives;
    let __VLS_styleScopedClasses;
    let __VLS_resolvedLocalAndGlobalComponents;
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("flex flex-col h-screen") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.header, __VLS_intrinsicElements.header)({ ...{ class: ("bg-white border-b border-gray-200 px-4 py-3") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("flex items-center justify-between max-w-4xl mx-auto") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("flex items-center space-x-3") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({ ...{ class: ("text-white font-semibold text-sm") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_elementAsFunction(__VLS_intrinsicElements.h1, __VLS_intrinsicElements.h1)({ ...{ class: ("text-xl font-semibold text-gray-900") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("flex items-center space-x-2 text-xs") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: (([
                'w-2 h-2 rounded-full',
                __VLS_ctx.isConnected ? 'bg-green-400' : 'bg-red-400',
            ])) }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({ ...{ class: ((__VLS_ctx.isConnected ? 'text-green-600' : 'text-red-600')) }, });
    (__VLS_ctx.isConnected
        ? __VLS_ctx.languageStore.isEnglish
            ? "Connected"
            : "接続済み"
        : __VLS_ctx.languageStore.isEnglish
            ? "Disconnected"
            : "切断済み");
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("flex items-center space-x-3") }, });
    // @ts-ignore
    [LanguageToggle,];
    // @ts-ignore
    const __VLS_0 = __VLS_asFunctionalComponent(LanguageToggle, new LanguageToggle({}));
    const __VLS_1 = __VLS_0({}, ...__VLS_functionalComponentArgsRest(__VLS_0));
    const __VLS_5 = __VLS_resolvedLocalAndGlobalComponents.RouterLink;
    /** @type { [typeof __VLS_components.RouterLink, typeof __VLS_components.RouterLink, ] } */
    // @ts-ignore
    const __VLS_6 = __VLS_asFunctionalComponent(__VLS_5, new __VLS_5({ to: ("/preferences"), ...{ class: ("btn-secondary text-sm") }, }));
    const __VLS_7 = __VLS_6({ to: ("/preferences"), ...{ class: ("btn-secondary text-sm") }, }, ...__VLS_functionalComponentArgsRest(__VLS_6));
    (__VLS_ctx.languageStore.isEnglish ? "Preferences" : "設定");
    __VLS_nonNullable(__VLS_10.slots).default;
    const __VLS_10 = __VLS_pickFunctionalComponentCtx(__VLS_5, __VLS_7);
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("flex-1 flex flex-col max-w-4xl mx-auto w-full") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ref: ("messagesContainer"), ...{ class: ("flex-1 overflow-y-auto p-4 space-y-4") }, });
    // @ts-ignore navigation for `const messagesContainer = ref()`
    __VLS_ctx.messagesContainer;
    if (!__VLS_ctx.chatStore.hasMessages) {
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("text-center text-gray-500 text-sm space-y-2") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        (__VLS_ctx.languageStore.isEnglish
            ? "Start a conversation with Noah about books and reading!"
            : "ノアと本や読書について会話を始めましょう！");
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("text-xs") }, });
        (__VLS_ctx.languageStore.isEnglish
            ? 'Try asking: "Can you recommend a good mystery novel?" or "I\'m feeling lucky!"'
            : "試しに聞いてみてください：「良いミステリー小説を教えて」または「何かおすすめして」");
    }
    for (const [message] of __VLS_getVForSourceType((__VLS_ctx.chatStore.sortedMessages))) {
        // @ts-ignore
        [ChatMessage,];
        // @ts-ignore
        const __VLS_11 = __VLS_asFunctionalComponent(ChatMessage, new ChatMessage({ key: ((message.id)), message: ((message)), }));
        const __VLS_12 = __VLS_11({ key: ((message.id)), message: ((message)), }, ...__VLS_functionalComponentArgsRest(__VLS_11));
    }
    // @ts-ignore
    [TypingIndicator,];
    // @ts-ignore
    const __VLS_16 = __VLS_asFunctionalComponent(TypingIndicator, new TypingIndicator({ isVisible: ((__VLS_ctx.isTyping)), }));
    const __VLS_17 = __VLS_16({ isVisible: ((__VLS_ctx.isTyping)), }, ...__VLS_functionalComponentArgsRest(__VLS_16));
    if (__VLS_ctx.chatStore.isLoading) {
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("flex justify-center") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600") }, });
    }
    if (__VLS_ctx.chatStore.error) {
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("bg-red-50 border border-red-200 text-red-700 px-4 py-3 mx-4") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("flex items-center justify-between") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({ ...{ class: ("text-sm") }, });
        (__VLS_ctx.chatStore.error);
        __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (__VLS_ctx.clearError) }, ...{ class: ("text-red-500 hover:text-red-700") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.svg, __VLS_intrinsicElements.svg)({ ...{ class: ("w-4 h-4") }, fill: ("none"), stroke: ("currentColor"), viewBox: ("0 0 24 24"), });
        __VLS_elementAsFunction(__VLS_intrinsicElements.path)({ "stroke-linecap": ("round"), "stroke-linejoin": ("round"), "stroke-width": ("2"), d: ("M6 18L18 6M6 6l12 12"), });
    }
    __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("border-t border-gray-200 bg-white p-4") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.form, __VLS_intrinsicElements.form)({ ...{ onSubmit: (__VLS_ctx.sendMessage) }, ...{ class: ("flex space-x-3") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.input)({ ...{ onKeydown: (__VLS_ctx.sendMessage) }, value: ((__VLS_ctx.messageInput)), type: ("text"), placeholder: ((__VLS_ctx.languageStore.isEnglish
            ? 'Ask Noah for book recommendations...'
            : 'ノアに本のおすすめを聞いてみてください...')), disabled: ((!__VLS_ctx.isConnected || __VLS_ctx.chatStore.isLoading)), ...{ class: ("flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ type: ("submit"), disabled: ((!__VLS_ctx.messageInput.trim() || !__VLS_ctx.isConnected || __VLS_ctx.chatStore.isLoading)), ...{ class: ("btn-primary disabled:opacity-50 disabled:cursor-not-allowed") }, });
    (__VLS_ctx.languageStore.isEnglish ? "Send" : "送信");
    __VLS_styleScopedClasses['flex'];
    __VLS_styleScopedClasses['flex-col'];
    __VLS_styleScopedClasses['h-screen'];
    __VLS_styleScopedClasses['bg-white'];
    __VLS_styleScopedClasses['border-b'];
    __VLS_styleScopedClasses['border-gray-200'];
    __VLS_styleScopedClasses['px-4'];
    __VLS_styleScopedClasses['py-3'];
    __VLS_styleScopedClasses['flex'];
    __VLS_styleScopedClasses['items-center'];
    __VLS_styleScopedClasses['justify-between'];
    __VLS_styleScopedClasses['max-w-4xl'];
    __VLS_styleScopedClasses['mx-auto'];
    __VLS_styleScopedClasses['flex'];
    __VLS_styleScopedClasses['items-center'];
    __VLS_styleScopedClasses['space-x-3'];
    __VLS_styleScopedClasses['w-8'];
    __VLS_styleScopedClasses['h-8'];
    __VLS_styleScopedClasses['bg-primary-600'];
    __VLS_styleScopedClasses['rounded-full'];
    __VLS_styleScopedClasses['flex'];
    __VLS_styleScopedClasses['items-center'];
    __VLS_styleScopedClasses['justify-center'];
    __VLS_styleScopedClasses['text-white'];
    __VLS_styleScopedClasses['font-semibold'];
    __VLS_styleScopedClasses['text-sm'];
    __VLS_styleScopedClasses['text-xl'];
    __VLS_styleScopedClasses['font-semibold'];
    __VLS_styleScopedClasses['text-gray-900'];
    __VLS_styleScopedClasses['flex'];
    __VLS_styleScopedClasses['items-center'];
    __VLS_styleScopedClasses['space-x-2'];
    __VLS_styleScopedClasses['text-xs'];
    __VLS_styleScopedClasses['flex'];
    __VLS_styleScopedClasses['items-center'];
    __VLS_styleScopedClasses['space-x-3'];
    __VLS_styleScopedClasses['btn-secondary'];
    __VLS_styleScopedClasses['text-sm'];
    __VLS_styleScopedClasses['flex-1'];
    __VLS_styleScopedClasses['flex'];
    __VLS_styleScopedClasses['flex-col'];
    __VLS_styleScopedClasses['max-w-4xl'];
    __VLS_styleScopedClasses['mx-auto'];
    __VLS_styleScopedClasses['w-full'];
    __VLS_styleScopedClasses['flex-1'];
    __VLS_styleScopedClasses['overflow-y-auto'];
    __VLS_styleScopedClasses['p-4'];
    __VLS_styleScopedClasses['space-y-4'];
    __VLS_styleScopedClasses['text-center'];
    __VLS_styleScopedClasses['text-gray-500'];
    __VLS_styleScopedClasses['text-sm'];
    __VLS_styleScopedClasses['space-y-2'];
    __VLS_styleScopedClasses['text-xs'];
    __VLS_styleScopedClasses['flex'];
    __VLS_styleScopedClasses['justify-center'];
    __VLS_styleScopedClasses['animate-spin'];
    __VLS_styleScopedClasses['rounded-full'];
    __VLS_styleScopedClasses['h-6'];
    __VLS_styleScopedClasses['w-6'];
    __VLS_styleScopedClasses['border-b-2'];
    __VLS_styleScopedClasses['border-primary-600'];
    __VLS_styleScopedClasses['bg-red-50'];
    __VLS_styleScopedClasses['border'];
    __VLS_styleScopedClasses['border-red-200'];
    __VLS_styleScopedClasses['text-red-700'];
    __VLS_styleScopedClasses['px-4'];
    __VLS_styleScopedClasses['py-3'];
    __VLS_styleScopedClasses['mx-4'];
    __VLS_styleScopedClasses['flex'];
    __VLS_styleScopedClasses['items-center'];
    __VLS_styleScopedClasses['justify-between'];
    __VLS_styleScopedClasses['text-sm'];
    __VLS_styleScopedClasses['text-red-500'];
    __VLS_styleScopedClasses['hover:text-red-700'];
    __VLS_styleScopedClasses['w-4'];
    __VLS_styleScopedClasses['h-4'];
    __VLS_styleScopedClasses['border-t'];
    __VLS_styleScopedClasses['border-gray-200'];
    __VLS_styleScopedClasses['bg-white'];
    __VLS_styleScopedClasses['p-4'];
    __VLS_styleScopedClasses['flex'];
    __VLS_styleScopedClasses['space-x-3'];
    __VLS_styleScopedClasses['flex-1'];
    __VLS_styleScopedClasses['border'];
    __VLS_styleScopedClasses['border-gray-300'];
    __VLS_styleScopedClasses['rounded-lg'];
    __VLS_styleScopedClasses['px-4'];
    __VLS_styleScopedClasses['py-2'];
    __VLS_styleScopedClasses['focus:outline-none'];
    __VLS_styleScopedClasses['focus:ring-2'];
    __VLS_styleScopedClasses['focus:ring-primary-500'];
    __VLS_styleScopedClasses['focus:border-transparent'];
    __VLS_styleScopedClasses['disabled:bg-gray-100'];
    __VLS_styleScopedClasses['disabled:cursor-not-allowed'];
    __VLS_styleScopedClasses['btn-primary'];
    __VLS_styleScopedClasses['disabled:opacity-50'];
    __VLS_styleScopedClasses['disabled:cursor-not-allowed'];
    var __VLS_slots;
    var __VLS_inheritedAttrs;
    const __VLS_refs = {
        "messagesContainer": __VLS_nativeElements['div'],
    };
    var $refs;
    return {
        slots: __VLS_slots,
        refs: $refs,
        attrs: {},
    };
}
;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            RouterLink: RouterLink,
            ChatMessage: ChatMessage,
            TypingIndicator: TypingIndicator,
            LanguageToggle: LanguageToggle,
            chatStore: chatStore,
            languageStore: languageStore,
            isConnected: isConnected,
            messageInput: messageInput,
            messagesContainer: messagesContainer,
            isTyping: isTyping,
            sendMessage: sendMessage,
            clearError: clearError,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
;
