<template>
  <div class="relative">
    <button
      @click="toggleDropdown"
      class="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors"
      :title="'Select language'"
    >
      <span class="text-lg">{{ languageStore.isEnglish ? "🇺🇸" : "🇯🇵" }}</span>
      <span>{{ languageStore.languageLabel }}</span>
      <svg
        class="w-4 h-4 ml-1 transition-transform"
        :class="{ 'rotate-180': isDropdownOpen }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M19 9l-7 7-7-7"
        />
      </svg>
    </button>

    <div
      v-if="isDropdownOpen"
      class="absolute right-0 mt-2 w-48 bg-white border border-gray-300 rounded-lg shadow-lg z-50"
    >
      <div class="py-1">
        <button
          @click="selectLanguage('english')"
          class="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          :class="{ 'bg-primary-50 text-primary-700': languageStore.isEnglish }"
        >
          <span class="text-lg mr-3">🇺🇸</span>
          <span>English</span>
          <svg
            v-if="languageStore.isEnglish"
            class="w-4 h-4 ml-auto text-primary-600"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fill-rule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clip-rule="evenodd"
            />
          </svg>
        </button>
        <button
          @click="selectLanguage('japanese')"
          class="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          :class="{
            'bg-primary-50 text-primary-700': languageStore.isJapanese,
          }"
        >
          <span class="text-lg mr-3">🇯🇵</span>
          <span>日本語</span>
          <svg
            v-if="languageStore.isJapanese"
            class="w-4 h-4 ml-auto text-primary-600"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fill-rule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clip-rule="evenodd"
            />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { useLanguageStore } from "@/stores/language";
import type { Language } from "@/stores/language";

const languageStore = useLanguageStore();
const isDropdownOpen = ref(false);

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value;
};

const selectLanguage = (language: Language) => {
  languageStore.setLanguage(language);
  isDropdownOpen.value = false;
};

// Close dropdown when clicking outside
const handleClickOutside = (event: Event) => {
  const target = event.target as HTMLElement;
  if (!target.closest(".relative")) {
    isDropdownOpen.value = false;
  }
};

onMounted(() => {
  document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
});
</script>
