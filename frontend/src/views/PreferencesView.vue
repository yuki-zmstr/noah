<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200 px-4 py-3">
      <div class="flex items-center justify-between max-w-4xl mx-auto">
        <div class="flex items-center space-x-3">
          <RouterLink to="/" class="text-gray-500 hover:text-gray-700">
            {{
              languageStore.isEnglish ? "← Back to Chat" : "← チャットに戻る"
            }}
          </RouterLink>
        </div>
        <h1 class="text-xl font-semibold text-gray-900">
          {{ languageStore.isEnglish ? "Reading Preferences" : "読書設定" }}
        </h1>
        <div class="flex items-center">
          <LanguageToggle />
        </div>
      </div>
    </header>

    <!-- Content -->
    <div class="max-w-4xl mx-auto p-6">
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">
          {{
            languageStore.isEnglish
              ? "Your Reading Profile"
              : "あなたの読書プロフィール"
          }}
        </h2>
        <p class="text-gray-600 mb-6">
          {{
            languageStore.isEnglish
              ? "Noah learns your preferences automatically, but you can view and adjust them here."
              : "ノアは自動的にあなたの好みを学習しますが、ここで確認・調整できます。"
          }}
        </p>

        <div class="space-y-6">
          <!-- Language Preferences -->
          <div>
            <h3 class="text-md font-medium text-gray-900 mb-2">
              {{
                languageStore.isEnglish ? "Language Preferences" : "言語設定"
              }}
            </h3>
            <div class="grid grid-cols-2 gap-4">
              <div class="border border-gray-200 rounded-lg p-4">
                <h4 class="font-medium text-gray-900">English</h4>
                <p class="text-sm text-gray-600">
                  {{
                    languageStore.isEnglish
                      ? "Reading Level: Intermediate"
                      : "読解レベル: 中級"
                  }}
                </p>
              </div>
              <div class="border border-gray-200 rounded-lg p-4">
                <h4 class="font-medium text-gray-900">日本語</h4>
                <p class="text-sm text-gray-600">
                  {{
                    languageStore.isEnglish
                      ? "Reading Level: Beginner"
                      : "読解レベル: 初級"
                  }}
                </p>
              </div>
            </div>
          </div>

          <!-- Favorite Genres -->
          <div>
            <h3 class="text-md font-medium text-gray-900 mb-2">
              {{
                languageStore.isEnglish ? "Favorite Genres" : "好きなジャンル"
              }}
            </h3>
            <div class="flex flex-wrap gap-2">
              <span
                class="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm"
              >
                {{
                  languageStore.isEnglish
                    ? "Science Fiction"
                    : "サイエンスフィクション"
                }}
              </span>
              <span
                class="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm"
              >
                {{ languageStore.isEnglish ? "Mystery" : "ミステリー" }}
              </span>
              <span
                class="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm"
              >
                {{
                  languageStore.isEnglish ? "Non-fiction" : "ノンフィクション"
                }}
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
import { useLanguageStore } from "@/stores/language";
import LanguageToggle from "@/components/LanguageToggle.vue";

const languageStore = useLanguageStore();
</script>
