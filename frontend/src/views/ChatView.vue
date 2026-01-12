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
          <h1 class="text-xl font-semibold text-gray-900">Noah</h1>
        </div>
        <RouterLink to="/preferences" class="btn-secondary text-sm">
          Preferences
        </RouterLink>
      </div>
    </header>

    <!-- Chat Container -->
    <div class="flex-1 flex flex-col max-w-4xl mx-auto w-full">
      <!-- Messages Area -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4">
        <div class="text-center text-gray-500 text-sm">
          Start a conversation with Noah about books and reading!
        </div>
      </div>

      <!-- Input Area -->
      <div class="border-t border-gray-200 bg-white p-4">
        <div class="flex space-x-3">
          <input
            type="text"
            placeholder="Ask Noah for book recommendations..."
            class="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <button class="btn-primary">Send</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
</script>
