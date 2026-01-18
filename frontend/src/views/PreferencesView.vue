<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200 px-4 py-3">
      <div class="flex items-center justify-between max-w-6xl mx-auto">
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
        <div class="flex items-center space-x-3">
          <button
            @click="refreshData"
            :disabled="preferencesStore.isLoading"
            class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {{ languageStore.isEnglish ? "Refresh" : "更新" }}
          </button>
          <LanguageToggle />
        </div>
      </div>
    </header>

    <!-- Loading State -->
    <div
      v-if="preferencesStore.isLoading && !preferencesStore.hasTransparencyData"
      class="flex items-center justify-center min-h-96"
    >
      <div class="text-center">
        <div
          class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"
        ></div>
        <p class="text-gray-600">
          {{
            languageStore.isEnglish
              ? "Loading your preferences..."
              : "設定を読み込み中..."
          }}
        </p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="preferencesStore.error" class="max-w-6xl mx-auto p-6">
      <div class="bg-red-50 border border-red-200 rounded-lg p-4">
        <div class="flex">
          <svg
            class="w-5 h-5 text-red-400 mt-0.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">
              {{
                languageStore.isEnglish
                  ? "Error loading preferences"
                  : "設定の読み込みエラー"
              }}
            </h3>
            <p class="mt-1 text-sm text-red-700">
              {{ preferencesStore.error }}
            </p>
            <button
              @click="refreshData"
              class="mt-2 text-sm text-red-800 underline hover:text-red-900"
            >
              {{ languageStore.isEnglish ? "Try again" : "再試行" }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div
      v-else-if="preferencesStore.hasTransparencyData"
      class="max-w-6xl mx-auto p-6"
    >
      <!-- Overview Section -->
      <div
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6"
      >
        <h2 class="text-lg font-semibold text-gray-900 mb-4">
          {{
            languageStore.isEnglish
              ? "Your Reading Profile"
              : "あなたの読書プロフィール"
          }}
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div class="text-center p-3 bg-gray-50 rounded-lg">
            <div class="text-2xl font-bold text-blue-600">
              {{ preferencesStore.transparencyData?.data_points_analyzed || 0 }}
            </div>
            <div class="text-gray-600">
              {{
                languageStore.isEnglish ? "Reading Sessions" : "読書セッション"
              }}
            </div>
          </div>
          <div class="text-center p-3 bg-gray-50 rounded-lg">
            <div class="text-2xl font-bold text-green-600">
              {{ preferencesStore.topicPreferences.length }}
            </div>
            <div class="text-gray-600">
              {{
                languageStore.isEnglish ? "Topic Preferences" : "トピック設定"
              }}
            </div>
          </div>
          <div class="text-center p-3 bg-gray-50 rounded-lg">
            <div class="text-2xl font-bold text-purple-600">
              {{ formatDate(preferencesStore.transparencyData?.last_updated) }}
            </div>
            <div class="text-gray-600">
              {{ languageStore.isEnglish ? "Last Updated" : "最終更新" }}
            </div>
          </div>
        </div>
        <p class="text-gray-600 mt-4">
          {{
            languageStore.isEnglish
              ? "Noah learns your preferences automatically from your reading behavior. You can view and adjust them below."
              : "ノアは読書行動から自動的に好みを学習します。以下で確認・調整できます。"
          }}
        </p>
      </div>

      <!-- Reading Levels Section -->
      <div
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6"
      >
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
          {{ languageStore.isEnglish ? "Reading Levels" : "読解レベル" }}
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ReadingLevelCard
            v-if="preferencesStore.readingLevels"
            language="english"
            :reading-level="preferencesStore.readingLevels.english"
            @update="handleReadingLevelUpdate"
          />
          <ReadingLevelCard
            v-if="preferencesStore.readingLevels"
            language="japanese"
            :reading-level="preferencesStore.readingLevels.japanese"
            @update="handleReadingLevelUpdate"
          />
        </div>
      </div>

      <!-- Topic Preferences Section -->
      <div
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6"
      >
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">
            {{ languageStore.isEnglish ? "Topic Preferences" : "トピック設定" }}
          </h3>
          <div class="flex space-x-2">
            <button
              @click="activeTopicFilter = 'all'"
              :class="
                activeTopicFilter === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700'
              "
              class="px-3 py-1 text-sm rounded transition-colors"
            >
              {{ languageStore.isEnglish ? "All" : "全て" }}
            </button>
            <button
              @click="activeTopicFilter = 'strong'"
              :class="
                activeTopicFilter === 'strong'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700'
              "
              class="px-3 py-1 text-sm rounded transition-colors"
            >
              {{ languageStore.isEnglish ? "Strong" : "強い" }}
            </button>
            <button
              @click="activeTopicFilter = 'moderate'"
              :class="
                activeTopicFilter === 'moderate'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700'
              "
              class="px-3 py-1 text-sm rounded transition-colors"
            >
              {{ languageStore.isEnglish ? "Moderate" : "中程度" }}
            </button>
          </div>
        </div>

        <div
          v-if="filteredTopicPreferences.length === 0"
          class="text-center py-8 text-gray-500"
        >
          {{
            languageStore.isEnglish
              ? "No topic preferences found. Start reading to build your profile!"
              : "トピック設定がありません。読書を始めてプロフィールを構築しましょう！"
          }}
        </div>

        <div
          v-else
          class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          <PreferenceItem
            v-for="topic in filteredTopicPreferences"
            :key="topic.topic"
            :name="topic.topic"
            :weight="topic.weight"
            :confidence="topic.confidence"
            :explanation="topic.explanation"
            :last-updated="topic.last_updated"
            :session-count="topic.related_sessions"
            @update="handleTopicUpdate"
          />
        </div>
      </div>

      <!-- Content Type Preferences Section -->
      <div
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6"
      >
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
          {{
            languageStore.isEnglish
              ? "Content Type Preferences"
              : "コンテンツタイプ設定"
          }}
        </h3>

        <div
          v-if="preferencesStore.contentTypePreferences.length === 0"
          class="text-center py-8 text-gray-500"
        >
          {{
            languageStore.isEnglish
              ? "No content type preferences yet."
              : "コンテンツタイプ設定がまだありません。"
          }}
        </div>

        <div
          v-else
          class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          <PreferenceItem
            v-for="contentType in preferencesStore.contentTypePreferences"
            :key="contentType.type"
            :name="contentType.type"
            :weight="contentType.preference"
            :explanation="contentType.explanation"
            :last-updated="contentType.last_updated"
            :session-count="contentType.sessions_count"
            @update="handleContentTypeUpdate"
          />
        </div>
      </div>

      <!-- Contextual Preferences Section -->
      <div
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6"
      >
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
          {{ languageStore.isEnglish ? "Contextual Patterns" : "文脈パターン" }}
        </h3>

        <div
          v-if="preferencesStore.contextualPreferences.length === 0"
          class="text-center py-8 text-gray-500"
        >
          {{
            languageStore.isEnglish
              ? "No contextual patterns detected yet."
              : "文脈パターンがまだ検出されていません。"
          }}
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-for="context in preferencesStore.contextualPreferences"
            :key="`${context.factor}:${context.value}`"
            class="border border-gray-200 rounded-lg p-4"
          >
            <div class="flex items-center justify-between mb-2">
              <h4 class="font-medium text-gray-900">
                {{ formatContextualPreference(context) }}
              </h4>
              <span
                :class="
                  context.weight > 0
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                "
                class="px-2 py-1 rounded-full text-xs font-medium"
              >
                {{
                  context.weight > 0
                    ? languageStore.isEnglish
                      ? "Favors"
                      : "好む"
                    : languageStore.isEnglish
                      ? "Avoids"
                      : "避ける"
                }}
              </span>
            </div>
            <p class="text-sm text-gray-600 mb-2">{{ context.explanation }}</p>
            <div class="text-xs text-gray-500">
              {{ languageStore.isEnglish ? "Based on" : "データ数:" }}
              {{ context.sessions_count }}
              {{ languageStore.isEnglish ? "sessions" : "セッション" }}
            </div>
          </div>
        </div>
      </div>

      <!-- Preference Evolution Section -->
      <div
        v-if="
          preferencesStore.hasEvolutionData &&
          preferencesStore.evolutionData?.evolution_detected
        "
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
      >
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
          {{ languageStore.isEnglish ? "Preference Evolution" : "設定の変化" }}
        </h3>

        <div class="space-y-3">
          <div
            v-for="trend in preferencesStore.evolutionData.trends"
            :key="`${trend.type}-${trend.item}`"
            class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
          >
            <div>
              <span class="font-medium">{{ trend.item }}</span>
              <span class="text-sm text-gray-600 ml-2">({{ trend.type }})</span>
            </div>
            <div class="flex items-center space-x-2">
              <span
                :class="
                  trend.direction === 'increasing'
                    ? 'text-green-600'
                    : 'text-red-600'
                "
                class="text-sm font-medium"
              >
                {{ trend.direction === "increasing" ? "↗" : "↘" }}
                {{ (trend.change * 100).toFixed(1) }}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="max-w-6xl mx-auto p-6">
      <div class="text-center py-12">
        <svg
          class="w-16 h-16 text-gray-400 mx-auto mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
          />
        </svg>
        <h3 class="text-lg font-medium text-gray-900 mb-2">
          {{
            languageStore.isEnglish
              ? "No preferences yet"
              : "まだ設定がありません"
          }}
        </h3>
        <p class="text-gray-600 mb-4">
          {{
            languageStore.isEnglish
              ? "Start chatting with Noah and reading content to build your personalized profile."
              : "ノアとチャットして読書を始めると、パーソナライズされたプロフィールが構築されます。"
          }}
        </p>
        <RouterLink
          to="/"
          class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          {{ languageStore.isEnglish ? "Start Chatting" : "チャットを始める" }}
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { RouterLink } from "vue-router";
import { useLanguageStore } from "@/stores/language";
import { usePreferencesStore } from "@/stores/preferences";
import LanguageToggle from "@/components/LanguageToggle.vue";
import PreferenceItem from "@/components/PreferenceItem.vue";
import ReadingLevelCard from "@/components/ReadingLevelCard.vue";
import type { ContextualPreference } from "@/types/preferences";

const languageStore = useLanguageStore();
const preferencesStore = usePreferencesStore();

// Local state
const activeTopicFilter = ref<"all" | "strong" | "moderate">("all");

// Mock user ID - in a real app, this would come from authentication
const userId = "user_123";

// Computed properties
const filteredTopicPreferences = computed(() => {
  const topics = preferencesStore.topicPreferences;

  switch (activeTopicFilter.value) {
    case "strong":
      return topics.filter((tp) => Math.abs(tp.weight) > 0.6);
    case "moderate":
      return topics.filter(
        (tp) => Math.abs(tp.weight) > 0.3 && Math.abs(tp.weight) <= 0.6,
      );
    default:
      return topics;
  }
});

// Methods
const formatDate = (dateString?: string): string => {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleDateString(languageStore.isEnglish ? "en-US" : "ja-JP");
};

const formatContextualPreference = (context: ContextualPreference): string => {
  const factor = context.factor.replace("_", " ");
  const value = context.value;
  return `${factor}: ${value}`
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

const refreshData = async () => {
  await preferencesStore.refreshData(userId);
};

const handleTopicUpdate = async (data: { name: string; weight: number }) => {
  try {
    await preferencesStore.overridePreference(userId, {
      type: "topic",
      key: data.name,
      value: data.weight,
    });
  } catch (error) {
    console.error("Failed to update topic preference:", error);
  }
};

const handleContentTypeUpdate = async (data: {
  name: string;
  weight: number;
}) => {
  try {
    await preferencesStore.overridePreference(userId, {
      type: "content_type",
      key: data.name,
      value: data.weight,
    });
  } catch (error) {
    console.error("Failed to update content type preference:", error);
  }
};

const handleReadingLevelUpdate = async (data: {
  language: "english" | "japanese";
  level: number;
}) => {
  try {
    if (!preferencesStore.readingLevels) return;

    const updatedLevels = { ...preferencesStore.readingLevels };
    updatedLevels[data.language] = {
      ...updatedLevels[data.language],
      level: data.level,
    };

    await preferencesStore.updateReadingLevels(userId, updatedLevels);
  } catch (error) {
    console.error("Failed to update reading level:", error);
  }
};

// Lifecycle
onMounted(async () => {
  await refreshData();
});
</script>
