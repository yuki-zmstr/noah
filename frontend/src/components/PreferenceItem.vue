<template>
  <div
    class="preference-item border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
  >
    <div class="flex items-center justify-between mb-2">
      <h4 class="font-medium text-gray-900">{{ displayName }}</h4>
      <div class="flex items-center space-x-2">
        <span
          :class="strengthClass"
          class="px-2 py-1 rounded-full text-xs font-medium"
        >
          {{ strengthLabel }}
        </span>
        <button
          v-if="editable"
          @click="toggleEdit"
          class="text-gray-400 hover:text-gray-600 transition-colors"
          :title="languageStore.isEnglish ? 'Edit preference' : '設定を編集'"
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
    </div>

    <!-- Weight/Preference Bar -->
    <div class="mb-3">
      <div class="flex items-center justify-between text-sm text-gray-600 mb-1">
        <span>{{ languageStore.isEnglish ? "Preference" : "好み" }}</span>
        <span>{{ formatWeight(weight) }}</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div
          :class="weightBarClass"
          class="h-2 rounded-full transition-all duration-300"
          :style="{
            width: `${Math.abs(weight) * 50}%`,
            marginLeft: weight < 0 ? `${50 - Math.abs(weight) * 50}%` : '50%',
          }"
        ></div>
      </div>
      <div class="flex justify-between text-xs text-gray-400 mt-1">
        <span>{{ languageStore.isEnglish ? "Dislike" : "嫌い" }}</span>
        <span>{{ languageStore.isEnglish ? "Neutral" : "中立" }}</span>
        <span>{{ languageStore.isEnglish ? "Like" : "好き" }}</span>
      </div>
    </div>

    <!-- Edit Mode -->
    <div v-if="isEditing" class="mb-3 p-3 bg-gray-50 rounded-lg">
      <label class="block text-sm font-medium text-gray-700 mb-2">
        {{ languageStore.isEnglish ? "Adjust preference:" : "好みを調整:" }}
      </label>
      <input
        v-model.number="editWeight"
        type="range"
        min="-1"
        max="1"
        step="0.1"
        class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
      />
      <div class="flex justify-between text-xs text-gray-500 mt-1">
        <span>-1.0</span>
        <span>{{ editWeight.toFixed(1) }}</span>
        <span>1.0</span>
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
    <p v-if="explanation" class="text-sm text-gray-600 mb-2">
      {{ explanation }}
    </p>

    <!-- Metadata -->
    <div v-if="showMetadata" class="text-xs text-gray-500 space-y-1">
      <div v-if="confidence !== undefined">
        {{ languageStore.isEnglish ? "Confidence:" : "信頼度:" }}
        {{ (confidence * 100).toFixed(0) }}%
      </div>
      <div v-if="lastUpdated">
        {{ languageStore.isEnglish ? "Last updated:" : "最終更新:" }}
        {{ formatDate(lastUpdated) }}
      </div>
      <div v-if="sessionCount !== undefined">
        {{ languageStore.isEnglish ? "Based on" : "データ数:" }}
        {{ sessionCount }}
        {{ languageStore.isEnglish ? "sessions" : "セッション" }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useLanguageStore } from "@/stores/language";

interface Props {
  name: string;
  weight: number;
  confidence?: number;
  explanation?: string;
  lastUpdated?: string;
  sessionCount?: number;
  editable?: boolean;
  showMetadata?: boolean;
}

interface Emits {
  (e: "update", data: { name: string; weight: number }): void;
}

const props = withDefaults(defineProps<Props>(), {
  editable: true,
  showMetadata: true,
});

const emit = defineEmits<Emits>();

const languageStore = useLanguageStore();

// Edit state
const isEditing = ref(false);
const editWeight = ref(props.weight);

// Computed properties
const displayName = computed(() => {
  // Capitalize and format the name
  return props.name
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
});

const strengthLabel = computed(() => {
  const absWeight = Math.abs(props.weight);
  if (absWeight > 0.6) {
    return languageStore.isEnglish ? "Strong" : "強い";
  } else if (absWeight > 0.3) {
    return languageStore.isEnglish ? "Moderate" : "中程度";
  } else {
    return languageStore.isEnglish ? "Weak" : "弱い";
  }
});

const strengthClass = computed(() => {
  const absWeight = Math.abs(props.weight);
  if (absWeight > 0.6) {
    return props.weight > 0
      ? "bg-green-100 text-green-800"
      : "bg-red-100 text-red-800";
  } else if (absWeight > 0.3) {
    return props.weight > 0
      ? "bg-blue-100 text-blue-800"
      : "bg-orange-100 text-orange-800";
  } else {
    return "bg-gray-100 text-gray-800";
  }
});

const weightBarClass = computed(() => {
  return props.weight > 0 ? "bg-green-500" : "bg-red-500";
});

// Methods
const formatWeight = (weight: number): string => {
  const sign = weight > 0 ? "+" : "";
  return `${sign}${weight.toFixed(2)}`;
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString(languageStore.isEnglish ? "en-US" : "ja-JP");
};

const toggleEdit = () => {
  isEditing.value = !isEditing.value;
  if (isEditing.value) {
    editWeight.value = props.weight;
  }
};

const saveEdit = () => {
  emit("update", { name: props.name, weight: editWeight.value });
  isEditing.value = false;
};

const cancelEdit = () => {
  editWeight.value = props.weight;
  isEditing.value = false;
};
</script>

<style scoped>
.preference-item {
  transition: all 0.2s ease-in-out;
}

.preference-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Custom range slider styling */
input[type="range"] {
  background: linear-gradient(
    to right,
    #ef4444 0%,
    #ef4444 50%,
    #10b981 50%,
    #10b981 100%
  );
}

input[type="range"]::-webkit-slider-thumb {
  appearance: none;
  height: 20px;
  width: 20px;
  border-radius: 50%;
  background: #374151;
  cursor: pointer;
  border: 2px solid #ffffff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

input[type="range"]::-moz-range-thumb {
  height: 20px;
  width: 20px;
  border-radius: 50%;
  background: #374151;
  cursor: pointer;
  border: 2px solid #ffffff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
</style>
