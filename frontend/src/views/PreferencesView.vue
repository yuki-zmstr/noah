<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200 px-4 py-3">
      <div class="flex items-center justify-between max-w-4xl mx-auto">
        <div class="flex items-center space-x-3">
          <RouterLink to="/" class="text-gray-500 hover:text-gray-700">
            ← Back to Chat
          </RouterLink>
        </div>
        <h1 class="text-xl font-semibold text-gray-900">Reading Preferences</h1>
        <div></div>
      </div>
    </header>

    <!-- Content -->
    <div class="max-w-4xl mx-auto p-6">
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">
          Your Reading Profile
        </h2>
        <p class="text-gray-600 mb-6">
          Noah learns your preferences automatically, but you can view and
          adjust them here.
        </p>

        <div class="space-y-6">
          <!-- Language Preferences -->
          <div>
            <h3 class="text-md font-medium text-gray-900 mb-2">
              Language Preferences
            </h3>
            <div class="grid grid-cols-2 gap-4">
              <div class="border border-gray-200 rounded-lg p-4">
                <h4 class="font-medium text-gray-900">English</h4>
                <p class="text-sm text-gray-600">Reading Level: Intermediate</p>
              </div>
              <div class="border border-gray-200 rounded-lg p-4">
                <h4 class="font-medium text-gray-900">Japanese</h4>
                <p class="text-sm text-gray-600">Reading Level: Beginner</p>
              </div>
            </div>
          </div>

          <!-- Favorite Genres -->
          <div>
            <h3 class="text-md font-medium text-gray-900 mb-2">
              Favorite Genres
            </h3>
            <div class="flex flex-wrap gap-2">
              <span
                class="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm"
              >
                Science Fiction
              </span>
              <span
                class="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm"
              >
                Mystery
              </span>
              <span
                class="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm"
              >
                Non-fiction
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
</script>
