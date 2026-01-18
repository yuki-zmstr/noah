<template>
  <div
    :class="[
      'flex',
      message.sender === 'user' ? 'justify-end' : 'justify-start',
    ]"
  >
    <div
      :class="[
        'chat-message',
        message.sender === 'user' ? 'chat-message-user' : 'chat-message-noah',
      ]"
    >
      <!-- Text Content -->
      <div v-if="message.type === 'text'" class="whitespace-pre-wrap">
        {{ message.content }}
      </div>

      <!-- Recommendation Content -->
      <div v-else-if="message.type === 'recommendation'" class="space-y-3">
        <div class="whitespace-pre-wrap">{{ message.content }}</div>

        <div v-if="message.metadata?.recommendations" class="space-y-2">
          <div
            v-for="rec in message.metadata.recommendations"
            :key="rec.id"
            class="border border-gray-200 rounded-lg p-3 bg-gray-50"
          >
            <div class="flex items-start space-x-3">
              <img
                v-if="rec.coverUrl"
                :src="rec.coverUrl"
                :alt="`Cover of ${rec.title}`"
                class="w-12 h-16 object-cover rounded"
              />
              <div class="flex-1 min-w-0">
                <h4 class="font-semibold text-gray-900 truncate">
                  {{ rec.title }}
                </h4>
                <p class="text-sm text-gray-600">by {{ rec.author }}</p>
                <p class="text-xs text-gray-500 mt-1">
                  {{ rec.readingLevel }} • {{ rec.estimatedReadingTime }} min
                  read
                </p>
                <p class="text-sm text-gray-700 mt-2 line-clamp-2">
                  {{ rec.description }}
                </p>

                <!-- Feedback and Action Buttons -->
                <div class="flex items-center space-x-2 mt-3">
                  <button
                    @click="handleFeedback(rec.id, 'interested')"
                    class="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                  >
                    👍 Interested
                  </button>
                  <button
                    @click="handleFeedback(rec.id, 'not_interested')"
                    class="text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                  >
                    👎 Not for me
                  </button>
                  <button
                    @click="handlePurchaseInquiry(rec.title, rec.author)"
                    class="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                  >
                    🛒 Where to buy?
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Purchase Links Content -->
      <div v-else-if="message.type === 'purchase_links'" class="space-y-3">
        <div class="whitespace-pre-wrap">{{ message.content }}</div>

        <div v-if="message.metadata?.purchaseLinks" class="space-y-2">
          <a
            v-for="link in message.metadata.purchaseLinks"
            :key="link.id"
            :href="link.url"
            target="_blank"
            rel="noopener noreferrer"
            class="block border border-gray-200 rounded-lg p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <div class="flex items-center justify-between">
              <div>
                <span class="font-medium text-gray-900">{{
                  link.displayText
                }}</span>
                <div class="text-xs text-gray-500 mt-1">
                  <span class="capitalize">{{
                    link.type.replace("_", " ")
                  }}</span>
                  <span v-if="link.format"> • {{ link.format }}</span>
                  <span v-if="link.price"> • {{ link.price }}</span>
                </div>
              </div>
              <div class="text-xs text-gray-400">
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
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
              </div>
            </div>
          </a>
        </div>
      </div>

      <!-- Timestamp -->
      <div
        :class="[
          'text-xs mt-2',
          message.sender === 'user' ? 'text-primary-200' : 'text-gray-400',
        ]"
      >
        {{ formatTime(message.timestamp) }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ChatMessage } from "@/types/chat";

interface Props {
  message: ChatMessage;
}

interface Emits {
  (
    e: "feedback",
    bookId: string,
    feedbackType: "interested" | "not_interested",
  ): void;
  (e: "purchaseInquiry", title: string, author: string): void;
}

defineProps<Props>();
const emit = defineEmits<Emits>();

const formatTime = (timestamp: Date) => {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(new Date(timestamp));
};

const handleFeedback = (
  bookId: string,
  feedbackType: "interested" | "not_interested",
) => {
  emit("feedback", bookId, feedbackType);
};

const handlePurchaseInquiry = (title: string, author: string) => {
  emit("purchaseInquiry", title, author);
};
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
