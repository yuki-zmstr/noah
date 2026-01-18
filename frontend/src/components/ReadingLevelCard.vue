<template>
  <div class="reading-level-card border border-gray-200 rounded-lg p-4">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-lg font-semibold text-gray-900">
        {{ language === "english" ? "English" : "日本語" }}
      </h3>
      <button
        v-if="editable"
        @click="toggleEdit"
        class="text-gray-400 hover:text-gray-600 transition-colors"
        :title="
          languageStore.isEnglish ? 'Edit reading level' : '読解レベルを編集'
        "
      >
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
            d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
          />
        </svg>
      </button>
    </div>

    <!-- Current Level Display -->
    <div class="mb-4">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700">
          {{ languageStore.isEnglish ? "Current Level:" : "現在のレベル:" }}
        </span>
        <span
          :class="levelBadgeClass"
          class="px-2 py-1 rounded-full text-xs font-medium"
        >
          {{ levelDescription }}
        </span>
      </div>

      <!-- Level Progress Bar -->
      <div class="w-full bg-gray-200 rounded-full h-3 mb-2">
        <div
          class="bg-blue-500 h-3 rounded-full transition-all duration-300"
          :style="{ width: `${levelPercentage}%` }"
        ></div>
      </div>

      <div class="flex justify-between text-xs text-gray-500">
        <span>{{ languageStore.isEnglish ? "Beginner" : "初級" }}</span>
        <span>{{ languageStore.isEnglish ? "Expert" : "上級" }}</span>
      </div>
    </div>

    <!-- Edit Mode -->
    <div v-if="isEditing" class="mb-4 p-3 bg-gray-50 rounded-lg">
      <label class="block text-sm font-medium text-gray-700 mb-2">
        {{
          languageStore.isEnglish
            ? "Adjust reading level:"
            : "読解レベルを調整:"
        }}
      </label>
      <input
        v-model.number="editLevel"
        type="range"
        :min="levelRange.min"
        :max="levelRange.max"
        :step="levelRange.step"
        class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
      />
      <div class="flex justify-between text-xs text-gray-500 mt-1">
        <span>{{ levelRange.min }}</span>
        <span>{{ editLevel.toFixed(language === "english" ? 1 : 2) }}</span>
        <span>{{ levelRange.max }}</span>
      </div>
      <div class="flex space-x-2 mt-3">
        <button
          @click="saveEdit"
          class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
        >
          {{ languageStore.isEnglish ? "Save" : "保存" }}
        </button>
        <button
          @click="cancelEdit"
          class="px-3 py-1 bg-gray-300 text-gray-700 text-sm rounded hover:bg-gray-400 transition-colors"
        >
          {{ languageStore.isEnglish ? "Cancel" : "キャンセル" }}
        </button>
      </div>
    </div>

    <!-- Explanation -->
    <p v-if="readingLevel.explanation" class="text-sm text-gray-600 mb-3">
      {{ readingLevel.explanation }}
    </p>

    <!-- Metadata -->
    <div class="text-xs text-gray-500 space-y-1">
      <div>
        {{ languageStore.isEnglish ? "Confidence:" : "信頼度:" }}
        <span :class="confidenceClass"
          >{{ (readingLevel.confidence * 100).toFixed(0) }}%</span
        >
      </div>
      <div>
        {{ languageStore.isEnglish ? "Assessments:" : "評価回数:" }}
        {{ readingLevel.assessment_count }}
      </div>
      <div v-if="readingLevel.last_assessment">
        {{ languageStore.isEnglish ? "Last assessed:" : "最終評価:" }}
        {{ formatDate(readingLevel.last_assessment) }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useLanguageStore } from "@/stores/language";
import type { ReadingLevel } from "@/types/preferences";

interface Props {
  language: "english" | "japanese";
  readingLevel: ReadingLevel;
  editable?: boolean;
}

interface Emits {
  (
    e: "update",
    data: { language: "english" | "japanese"; level: number },
  ): void;
}

const props = withDefaults(defineProps<Props>(), {
  editable: true,
});

const emit = defineEmits<Emits>();

const languageStore = useLanguageStore();

// Edit state
const isEditing = ref(false);
const editLevel = ref(props.readingLevel.level);

// Computed properties
const levelRange = computed(() => {
  if (props.language === "english") {
    return { min: 0, max: 20, step: 0.5 };
  } else {
    return { min: 0, max: 1, step: 0.05 };
  }
});

const levelDescription = computed(() => {
  const level = props.readingLevel.level;

  if (props.language === "english") {
    if (level < 6)
      return languageStore.isEnglish ? "Elementary" : "小学校レベル";
    if (level < 10)
      return languageStore.isEnglish ? "Middle School" : "中学校レベル";
    if (level < 14)
      return languageStore.isEnglish ? "High School" : "高校レベル";
    return languageStore.isEnglish ? "College" : "大学レベル";
  } else {
    if (level < 0.2) return languageStore.isEnglish ? "Basic" : "基礎";
    if (level < 0.4) return languageStore.isEnglish ? "Intermediate" : "中級";
    if (level < 0.6) return languageStore.isEnglish ? "Advanced" : "上級";
    return languageStore.isEnglish ? "Expert" : "専門";
  }
});

const levelBadgeClass = computed(() => {
  const level = props.readingLevel.level;
  const maxLevel = props.language === "english" ? 20 : 1;
  const percentage = (level / maxLevel) * 100;

  if (percentage < 25) return "bg-red-100 text-red-800";
  if (percentage < 50) return "bg-yellow-100 text-yellow-800";
  if (percentage < 75) return "bg-blue-100 text-blue-800";
  return "bg-green-100 text-green-800";
});

const levelPercentage = computed(() => {
  const level = props.readingLevel.level;
  const maxLevel = props.language === "english" ? 20 : 1;
  return Math.min(100, (level / maxLevel) * 100);
});

const confidenceClass = computed(() => {
  const confidence = props.readingLevel.confidence;
  if (confidence > 0.7) return "text-green-600 font-medium";
  if (confidence > 0.4) return "text-yellow-600 font-medium";
  return "text-red-600 font-medium";
});

// Methods
const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString(languageStore.isEnglish ? "en-US" : "ja-JP");
};

const toggleEdit = () => {
  isEditing.value = !isEditing.value;
  if (isEditing.value) {
    editLevel.value = props.readingLevel.level;
  }
};

const saveEdit = () => {
  emit("update", { language: props.language, level: editLevel.value });
  isEditing.value = false;
};

const cancelEdit = () => {
  editLevel.value = props.readingLevel.level;
  isEditing.value = false;
};
</script>

<style scoped>
.reading-level-card {
  transition: all 0.2s ease-in-out;
}

.reading-level-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Custom range slider styling */
input[type="range"]::-webkit-slider-thumb {
  appearance: none;
  height: 20px;
  width: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid #ffffff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

input[type="range"]::-moz-range-thumb {
  height: 20px;
  width: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid #ffffff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
</style>
