import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
export const useLanguageStore = defineStore('language', () => {
    // State
    const currentLanguage = ref('english');
    // Getters
    const isEnglish = computed(() => currentLanguage.value === 'english');
    const isJapanese = computed(() => currentLanguage.value === 'japanese');
    const languageLabel = computed(() => {
        return currentLanguage.value === 'english' ? 'English' : '日本語';
    });
    // Actions
    const setLanguage = (language) => {
        currentLanguage.value = language;
        // Store in localStorage for persistence
        localStorage.setItem('noah-language', language);
    };
    const toggleLanguage = () => {
        const newLanguage = currentLanguage.value === 'english' ? 'japanese' : 'english';
        setLanguage(newLanguage);
    };
    const initializeLanguage = () => {
        // Load from localStorage or default to English
        const stored = localStorage.getItem('noah-language');
        if (stored && (stored === 'english' || stored === 'japanese')) {
            currentLanguage.value = stored;
        }
    };
    return {
        // State
        currentLanguage,
        // Getters
        isEnglish,
        isJapanese,
        languageLabel,
        // Actions
        setLanguage,
        toggleLanguage,
        initializeLanguage
    };
});
