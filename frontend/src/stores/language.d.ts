export type Language = 'english' | 'japanese';
export declare const useLanguageStore: import("pinia").StoreDefinition<"language", Pick<{
    currentLanguage: import("vue").Ref<Language, Language>;
    isEnglish: import("vue").ComputedRef<boolean>;
    isJapanese: import("vue").ComputedRef<boolean>;
    languageLabel: import("vue").ComputedRef<"English" | "日本語">;
    setLanguage: (language: Language) => void;
    toggleLanguage: () => void;
    initializeLanguage: () => void;
}, "currentLanguage">, Pick<{
    currentLanguage: import("vue").Ref<Language, Language>;
    isEnglish: import("vue").ComputedRef<boolean>;
    isJapanese: import("vue").ComputedRef<boolean>;
    languageLabel: import("vue").ComputedRef<"English" | "日本語">;
    setLanguage: (language: Language) => void;
    toggleLanguage: () => void;
    initializeLanguage: () => void;
}, "isEnglish" | "isJapanese" | "languageLabel">, Pick<{
    currentLanguage: import("vue").Ref<Language, Language>;
    isEnglish: import("vue").ComputedRef<boolean>;
    isJapanese: import("vue").ComputedRef<boolean>;
    languageLabel: import("vue").ComputedRef<"English" | "日本語">;
    setLanguage: (language: Language) => void;
    toggleLanguage: () => void;
    initializeLanguage: () => void;
}, "setLanguage" | "toggleLanguage" | "initializeLanguage">>;
