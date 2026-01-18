<template>
  <div class="flex flex-col h-screen">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200 px-4 py-3">
      <div class="flex items-center justify-between max-w-4xl mx-auto">
        <div class="flex items-center space-x-3">
          <div
            class="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center"
          >
            <span class="text-white font-semibold text-sm">N</span>
          </div>
          <div>
            <h1 class="text-xl font-semibold text-gray-900">Noah</h1>
            <div class="flex items-center space-x-2 text-xs">
              <div
                :class="[
                  'w-2 h-2 rounded-full',
                  isConnected ? 'bg-green-400' : 'bg-red-400',
                ]"
              ></div>
              <span :class="isConnected ? 'text-green-600' : 'text-red-600'">
                {{
                  isConnected
                    ? languageStore.isEnglish
                      ? "Connected"
                      : "接続済み"
                    : languageStore.isEnglish
                      ? "Disconnected"
                      : "切断済み"
                }}
              </span>
            </div>
          </div>
        </div>
        <div class="flex items-center space-x-3">
          <LanguageToggle />
          <RouterLink to="/preferences" class="btn-secondary text-sm">
            {{ languageStore.isEnglish ? "Preferences" : "設定" }}
          </RouterLink>
        </div>
      </div>
    </header>

    <!-- Chat Container -->
    <div class="flex-1 flex flex-col max-w-4xl mx-auto w-full">
      <!-- Messages Area -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
        <!-- Welcome Message -->
        <div
          v-if="!chatStore.hasMessages"
          class="text-center text-gray-500 text-sm space-y-2"
        >
          <div>
            {{
              languageStore.isEnglish
                ? "Start a conversation with Noah about books and reading!"
                : "ノアと本や読書について会話を始めましょう！"
            }}
          </div>
          <div class="text-xs">
            {{
              languageStore.isEnglish
                ? 'Try asking: "Can you recommend a good mystery novel?" or "I\'m feeling lucky!"'
                : "試しに聞いてみてください：「良いミステリー小説を教えて」または「何かおすすめして」"
            }}
          </div>
        </div>

        <!-- Messages -->
        <ChatMessage
          v-for="message in chatStore.sortedMessages"
          :key="message.id"
          :message="message"
          @feedback="handleRecommendationFeedback"
          @purchase-inquiry="handlePurchaseInquiry"
        />

        <!-- Typing Indicator -->
        <TypingIndicator :is-visible="isTyping" />

        <!-- Loading Indicator -->
        <div v-if="chatStore.isLoading" class="flex justify-center">
          <div
            class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"
          ></div>
        </div>
      </div>

      <!-- Error Message -->
      <div
        v-if="chatStore.error"
        class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 mx-4"
      >
        <div class="flex items-center justify-between">
          <span class="text-sm">{{ chatStore.error }}</span>
          <button @click="clearError" class="text-red-500 hover:text-red-700">
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>

      <!-- Input Area -->
      <div class="border-t border-gray-200 bg-white p-4">
        <!-- Discovery Mode Button -->
        <div class="flex justify-center mb-3">
          <button
            @click="activateDiscoveryMode"
            :disabled="!isConnected || chatStore.isLoading"
            class="text-sm px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-full hover:from-purple-600 hover:to-pink-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg"
          >
            ✨
            {{
              languageStore.isEnglish
                ? "I'm feeling lucky!"
                : "何かおすすめして！"
            }}
          </button>
        </div>

        <form @submit.prevent="sendMessage" class="flex space-x-3">
          <input
            v-model="messageInput"
            type="text"
            :placeholder="
              languageStore.isEnglish
                ? 'Ask Noah for book recommendations...'
                : 'ノアに本のおすすめを聞いてみてください...'
            "
            :disabled="!isConnected || chatStore.isLoading"
            class="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            @keydown.enter.prevent="sendMessage"
          />
          <button
            type="submit"
            :disabled="
              !messageInput.trim() || !isConnected || chatStore.isLoading
            "
            class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ languageStore.isEnglish ? "Send" : "送信" }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from "vue";
import { RouterLink } from "vue-router";
import { useChatStore } from "@/stores/chat";
import { useLanguageStore } from "@/stores/language";
import { useWebSocket } from "@/composables/useWebSocket";
import ChatMessage from "@/components/ChatMessage.vue";
import TypingIndicator from "@/components/TypingIndicator.vue";
import LanguageToggle from "@/components/LanguageToggle.vue";
import type { ChatMessage as ChatMessageType } from "@/types/chat";

// Store and composables
const chatStore = useChatStore();
const languageStore = useLanguageStore();
const {
  isConnected,
  connectionError,
  sendMessage: sendWebSocketMessage,
  onMessage,
  onMessageChunk,
  onRecommendations,
  onPurchaseLinks,
  onMessageComplete,
  onTyping,
  onConversationHistory,
  joinSession,
} = useWebSocket();

// Reactive state
const messageInput = ref("");
const messagesContainer = ref<HTMLElement>();
const isTyping = ref(false);
const typingTimeout = ref<number>();
const currentStreamingMessage = ref<ChatMessageType | null>(null);

// Computed properties from store - use store directly for reactivity

// Mock user ID for development
const userId = "user_" + Math.random().toString(36).substr(2, 9);

// Methods
const sendMessage = async () => {
  const message = messageInput.value.trim();
  if (!message || !isConnected.value) return;

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
};

// WebSocket event handlers
onMessage((message: ChatMessageType) => {
  chatStore.addMessage(message);
  nextTick(() => scrollToBottom());
});

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

const clearError = () => {
  chatStore.setError(null);
};

const handleRecommendationFeedback = (
  bookId: string,
  feedbackType: "interested" | "not_interested",
) => {
  // Send feedback to backend via WebSocket
  if (chatStore.currentSession && isConnected.value) {
    const feedbackMessage =
      feedbackType === "interested"
        ? `I'm interested in this book recommendation (ID: ${bookId})`
        : `This book recommendation isn't for me (ID: ${bookId})`;

    sendWebSocketMessage(feedbackMessage, chatStore.currentSession.sessionId, {
      type: "feedback",
      bookId,
      feedbackType,
      language: languageStore.currentLanguage,
    });
  }
};

const handlePurchaseInquiry = (title: string, author: string) => {
  // Send purchase inquiry to backend via WebSocket
  if (chatStore.currentSession && isConnected.value) {
    const inquiryMessage = `Where can I buy "${title}" by ${author}?`;

    sendWebSocketMessage(inquiryMessage, chatStore.currentSession.sessionId, {
      type: "purchase_inquiry",
      bookTitle: title,
      bookAuthor: author,
      language: languageStore.currentLanguage,
    });
  }
};

const activateDiscoveryMode = () => {
  // Send discovery mode activation message
  if (chatStore.currentSession && isConnected.value) {
    const discoveryMessage = languageStore.isEnglish
      ? "I'm feeling lucky! Surprise me with something new to read."
      : "何かおすすめして！新しい本を教えて。";

    // Add user message to chat
    chatStore.addUserMessage(discoveryMessage);

    sendWebSocketMessage(discoveryMessage, chatStore.currentSession.sessionId, {
      type: "discovery_mode",
      language: languageStore.currentLanguage,
    });

    // Scroll to bottom
    nextTick(() => scrollToBottom());
  }
};

// Handle streaming message chunks
onMessageChunk((chunk) => {
  if (!currentStreamingMessage.value) {
    // Start a new streaming message with the first chunk
    currentStreamingMessage.value = chatStore.addStreamingMessage(
      chunk.content,
    );
  } else {
    // Append new chunk to existing streaming message
    chatStore.appendToStreamingMessage(
      currentStreamingMessage.value.id,
      chunk.content,
    );
  }

  nextTick(() => scrollToBottom());
});

// Handle recommendations
onRecommendations((data) => {
  if (currentStreamingMessage.value) {
    const messageType = data.is_discovery ? "recommendation" : "recommendation";
    chatStore.updateStreamingMessage(
      currentStreamingMessage.value.id,
      currentStreamingMessage.value.content,
      { recommendations: data.recommendations },
    );
    // Update message type
    const messageIndex = chatStore.messages.findIndex(
      (msg) => msg.id === currentStreamingMessage.value?.id,
    );
    if (messageIndex !== -1) {
      chatStore.messages[messageIndex].type = messageType;
    }
  }
  nextTick(() => scrollToBottom());
});

// Handle purchase links
onPurchaseLinks((data) => {
  if (currentStreamingMessage.value) {
    chatStore.updateStreamingMessage(
      currentStreamingMessage.value.id,
      currentStreamingMessage.value.content,
      { purchaseLinks: data.purchase_links },
    );
    // Update message type
    const messageIndex = chatStore.messages.findIndex(
      (msg) => msg.id === currentStreamingMessage.value?.id,
    );
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
  // Clear existing messages first
  chatStore.clearMessages();

  // Load historical messages
  data.messages.forEach((msg) => {
    chatStore.addMessage({
      content: msg.content,
      sender: msg.sender as "user" | "noah",
      type: (msg.type as ChatMessageType["type"]) || "text",
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

// Watch connection status and show appropriate messages
watch(isConnected, (connected, wasConnected) => {
  if (connected && wasConnected === false) {
    // Just reconnected
    chatStore.setError(null);
  } else if (!connected && wasConnected === true) {
    // Just disconnected
    chatStore.setError("Connection lost. Attempting to reconnect...");
  }
});

// Initialize on mount
onMounted(() => {
  languageStore.initializeLanguage();
  chatStore.initializeSession(userId);

  // Join WebSocket session when connected
  watch(
    isConnected,
    (connected) => {
      if (connected && chatStore.currentSession) {
        joinSession(chatStore.currentSession.sessionId, userId);
      }
    },
    { immediate: true },
  );
});
</script>
