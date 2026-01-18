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
                  !isStreaming && !streamError
                    ? 'bg-green-400'
                    : streamError
                      ? 'bg-red-400'
                      : 'bg-yellow-400',
                ]"
              ></div>
              <span
                :class="
                  !isStreaming && !streamError
                    ? 'text-green-600'
                    : streamError
                      ? 'text-red-600'
                      : 'text-yellow-600'
                "
              >
                {{
                  streamError
                    ? languageStore.isEnglish
                      ? "Error"
                      : "エラー"
                    : isStreaming
                      ? languageStore.isEnglish
                        ? "Streaming"
                        : "ストリーミング中"
                      : languageStore.isEnglish
                        ? "Ready"
                        : "準備完了"
                }}
              </span>
            </div>
          </div>
        </div>
        <div class="flex items-center space-x-3">
          <span class="text-sm text-gray-600">{{ authStore.userEmail }}</span>
          <LanguageToggle />
          <RouterLink to="/preferences" class="btn-secondary text-sm">
            {{ languageStore.isEnglish ? "Preferences" : "設定" }}
          </RouterLink>
          <button @click="handleLogout" class="btn-secondary text-sm">
            {{ languageStore.isEnglish ? "Logout" : "ログアウト" }}
          </button>
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
                ? `Welcome back, ${authStore.user?.name || "there"}! Start a conversation with Noah about books and reading!`
                : `おかえりなさい、${authStore.user?.name || "さん"}！ノアと本や読書について会話を始めましょう！`
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

        <!-- Streaming Indicator -->
        <div
          v-if="isStreaming"
          class="flex items-center space-x-2 text-gray-500 text-sm"
        >
          <div
            class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"
          ></div>
          <span>{{
            languageStore.isEnglish
              ? "Noah is thinking..."
              : "ノアが考えています..."
          }}</span>
        </div>

        <!-- Typing Indicator -->
        <!-- <TypingIndicator :is-visible="isTyping" /> -->

        <!-- Loading Indicator -->
        <div v-if="chatStore.isLoading" class="flex justify-center">
          <div
            class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"
          ></div>
        </div>
      </div>

      <!-- Error Message -->
      <div
        v-if="chatStore.error || streamError"
        class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 mx-4"
      >
        <div class="flex items-center justify-between">
          <span class="text-sm">{{ chatStore.error || streamError }}</span>
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
            :disabled="isStreaming || chatStore.isLoading"
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
            :disabled="isStreaming || chatStore.isLoading"
            class="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            @keydown.enter.prevent="sendMessage"
          />
          <button
            type="submit"
            :disabled="
              !messageInput.trim() || isStreaming || chatStore.isLoading
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
import { RouterLink, useRouter } from "vue-router";
import { useChatStore } from "@/stores/chat";
import { useAuthStore } from "@/stores/auth";
import { useLanguageStore } from "@/stores/language";
import { useHttpStreaming } from "@/composables/useHttpStreaming";
import ChatMessage from "@/components/ChatMessage.vue";
import LanguageToggle from "@/components/LanguageToggle.vue";
import type { ChatMessage as ChatMessageType } from "@/types/chat";

// Store and composables
const router = useRouter();
const chatStore = useChatStore();
const authStore = useAuthStore();
const languageStore = useLanguageStore();
const {
  isStreaming,
  streamError,
  sendMessage: sendHttpMessage,
  getConversationHistory,
  updatePreferences,
  onContentChunk,
  onRecommendations,
  onComplete,
  onError,
} = useHttpStreaming();

// Reactive state
const messageInput = ref("");
const messagesContainer = ref<HTMLElement>();
const currentStreamingMessage = ref<ChatMessageType | null>(null);

// Methods
const sendMessage = async () => {
  const message = messageInput.value.trim();
  if (!message || isStreaming.value || !authStore.userId) return;

  // Add user message to store
  chatStore.addUserMessage(message);
  messageInput.value = "";

  // Send via HTTP streaming
  if (chatStore.currentSession) {
    try {
      await sendHttpMessage(
        message,
        chatStore.currentSession.sessionId,
        authStore.userId,
        {
          language: languageStore.currentLanguage,
        },
      );
    } catch (error) {
      console.error("Error sending message:", error);
      chatStore.setError("Failed to send message. Please try again.");
    }
  }

  // Scroll to bottom
  await nextTick();
  scrollToBottom();
};

const handleLogout = () => {
  // Clear chat data for current user
  chatStore.clearAllUserData();

  // Logout user
  authStore.logout();

  // Redirect to login
  router.push("/login");
};

const clearError = () => {
  chatStore.setError(null);
};

const handleRecommendationFeedback = async (
  bookId: string,
  feedbackType: "interested" | "not_interested",
) => {
  // Send feedback via HTTP streaming
  if (chatStore.currentSession && !isStreaming.value && authStore.userId) {
    const feedbackMessage =
      feedbackType === "interested"
        ? `I'm interested in this book recommendation (ID: ${bookId})`
        : `This book recommendation isn't for me (ID: ${bookId})`;

    try {
      await sendHttpMessage(
        feedbackMessage,
        chatStore.currentSession.sessionId,
        authStore.userId,
        {
          type: "feedback",
          bookId,
          feedbackType,
          language: languageStore.currentLanguage,
        },
      );
    } catch (error) {
      console.error("Error sending feedback:", error);
      chatStore.setError("Failed to send feedback. Please try again.");
    }
  }
};

const handlePurchaseInquiry = async (title: string, author: string) => {
  // Send purchase inquiry via HTTP streaming
  if (chatStore.currentSession && !isStreaming.value && authStore.userId) {
    const inquiryMessage = `Where can I buy "${title}" by ${author}?`;

    try {
      await sendHttpMessage(
        inquiryMessage,
        chatStore.currentSession.sessionId,
        authStore.userId,
        {
          type: "purchase_inquiry",
          bookTitle: title,
          bookAuthor: author,
          language: languageStore.currentLanguage,
        },
      );
    } catch (error) {
      console.error("Error sending purchase inquiry:", error);
      chatStore.setError("Failed to send purchase inquiry. Please try again.");
    }
  }
};

const activateDiscoveryMode = async () => {
  // Send discovery mode activation message
  if (chatStore.currentSession && !isStreaming.value && authStore.userId) {
    const discoveryMessage = languageStore.isEnglish
      ? "I'm feeling lucky! Surprise me with something new to read."
      : "何かおすすめして！新しい本を教えて。";

    // Add user message to chat
    chatStore.addUserMessage(discoveryMessage);

    try {
      await sendHttpMessage(
        discoveryMessage,
        chatStore.currentSession.sessionId,
        authStore.userId,
        {
          type: "discovery_mode",
          language: languageStore.currentLanguage,
        },
      );
    } catch (error) {
      console.error("Error activating discovery mode:", error);
      chatStore.setError(
        "Failed to activate discovery mode. Please try again.",
      );
    }

    // Scroll to bottom
    nextTick(() => scrollToBottom());
  }
};

const loadConversationHistory = async () => {
  if (!chatStore.currentSession) return;

  try {
    chatStore.setLoading(true);
    const messages = await getConversationHistory(
      chatStore.currentSession.sessionId,
    );

    // Clear existing messages and load history
    chatStore.clearMessages();
    messages.forEach((msg) => chatStore.addMessage(msg));

    nextTick(() => scrollToBottom());
  } catch (error) {
    console.error("Error loading conversation history:", error);
    chatStore.setError("Failed to load conversation history.");
  } finally {
    chatStore.setLoading(false);
  }
};

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

// HTTP Streaming event handlers
onContentChunk((chunk) => {
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
      chatStore.messages[messageIndex].type = "recommendation";
    }
  }
  nextTick(() => scrollToBottom());
});

// Handle message completion
onComplete((data) => {
  if (currentStreamingMessage.value) {
    // Finalize the streaming message (content is already accumulated from chunks)
    chatStore.finalizeStreamingMessage(currentStreamingMessage.value.id);
    currentStreamingMessage.value = null;
  }
  nextTick(() => scrollToBottom());
});

// Handle streaming errors
onError((data) => {
  if (currentStreamingMessage.value) {
    // Update the streaming message with error content
    chatStore.updateStreamingMessage(
      currentStreamingMessage.value.id,
      data.content,
    );
    chatStore.finalizeStreamingMessage(currentStreamingMessage.value.id);
    currentStreamingMessage.value = null;
  } else {
    // Add error as a new message
    chatStore.addNoahMessage(data.content, "text");
  }
  nextTick(() => scrollToBottom());
});

// Watch for stream errors
watch(streamError, (error) => {
  if (error) {
    chatStore.setError(`Streaming error: ${error}`);
  }
});

// Initialize on mount
onMounted(async () => {
  // Ensure user is authenticated
  if (!authStore.isAuthenticated) {
    router.push("/login");
    return;
  }

  languageStore.initializeLanguage();

  // Initialize chat session with authenticated user
  chatStore.initializeSession(authStore.userId);

  // Load conversation history
  await loadConversationHistory();
});
</script>
