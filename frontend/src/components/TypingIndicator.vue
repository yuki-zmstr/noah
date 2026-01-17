<template>
  <div v-if="isVisible" class="flex justify-start">
    <div class="chat-message chat-message-noah">
      <div class="flex items-center space-x-2">
        <div class="flex space-x-1">
          <div
            v-for="i in 3"
            :key="i"
            :class="[
              'w-2 h-2 bg-gray-400 rounded-full animate-pulse',
              `animation-delay-${i * 200}`,
            ]"
            :style="{ animationDelay: `${i * 200}ms` }"
          ></div>
        </div>
        <span class="text-sm text-gray-500">Noah is typing...</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  isVisible: boolean;
}

defineProps<Props>();
</script>

<style scoped>
@keyframes pulse {
  0%,
  70%,
  100% {
    opacity: 0.4;
  }
  35% {
    opacity: 1;
  }
}

.animate-pulse {
  animation: pulse 1.4s infinite ease-in-out;
}
</style>
