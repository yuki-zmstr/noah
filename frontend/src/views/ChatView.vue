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

  // Simulate Noah's response for development (remove when backend is ready)
  simulateNoahResponse(message);
};

const simulateNoahResponse = (userMessage: string) => {
  // Show typing indicator
  isTyping.value = true;

  setTimeout(
    () => {
      isTyping.value = false;

      // Generate mock response based on user message - match backend responses
      let response =
        "I'm Noah, your reading companion. How can I help you discover your next great read?";
      let messageType: ChatMessageType["type"] = "text";
      let metadata: ChatMessageType["metadata"] = undefined;

      if (
        userMessage.toLowerCase().includes("recommend") ||
        userMessage.toLowerCase().includes("book")
      ) {
        response =
          "I'd be happy to recommend some books for you! What genres or topics interest you?";
        messageType = "recommendation";
        metadata = {
          recommendations: [
            {
              id: "book_1",
              title: "The Seven Husbands of Evelyn Hugo",
              author: "Taylor Jenkins Reid",
              description:
                "A captivating novel about a reclusive Hollywood icon who finally decides to tell her story.",
              interestScore: 0.92,
              readingLevel: "Intermediate",
              estimatedReadingTime: 420,
            },
            {
              id: "book_2",
              title: "Educated",
              author: "Tara Westover",
              description:
                "A powerful memoir about education, family, and the struggle between loyalty and independence.",
              interestScore: 0.88,
              readingLevel: "Advanced",
              estimatedReadingTime: 380,
            },
          ],
        };
      } else if (
        userMessage.toLowerCase().includes("lucky") ||
        userMessage.toLowerCase().includes("discover")
      ) {
        response =
          "Let's explore something new! I'll find some books outside your usual preferences.";
        messageType = "recommendation";
        metadata = {
          recommendations: [
            {
              id: "book_discovery",
              title: "Klara and the Sun",
              author: "Kazuo Ishiguro",
              description:
                "A thought-provoking story told from the perspective of an artificial friend.",
              interestScore: 0.75,
              readingLevel: "Intermediate",
              estimatedReadingTime: 300,
            },
          ],
        };
      } else if (
        userMessage.toLowerCase().includes("buy") ||
        userMessage.toLowerCase().includes("purchase")
      ) {
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
    },
    1500 + Math.random() * 1000,
  ); // Random delay between 1.5-2.5 seconds
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
onMessage((message: ChatMessageType) => {
  chatStore.addMessage(message);
  nextTick(() => scrollToBottom());
});

// Handle streaming message chunks
onMessageChunk((chunk) => {
  if (!currentStreamingMessage.value) {
    // Start a new streaming message with the first chunk
    currentStreamingMessage.value = chatStore.addStreamingMessage(
      chunk.content,
    );
  } else {
    // Append new chunk to existing streaming message with a space separator
    chatStore.appendToStreamingMessage(
      currentStreamingMessage.value.id,
      " " + chunk.content,
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
