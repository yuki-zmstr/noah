<template>
  <button
    @click="toggleLanguage"
    class="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors"
    :title="
      languageStore.isEnglish ? 'Switch to Japanese' : 'Switch to English'
    "
  >
    <span class="text-lg">{{ languageStore.isEnglish ? "🇺🇸" : "🇯🇵" }}</span>
    <span>{{ languageStore.languageLabel }}</span>
  </button>
</template>

<script setup lang="ts">
import { useLanguageStore } from "@/stores/language";

const languageStore = useLanguageStore();
const { toggleLanguage } = languageStore;
</script>
