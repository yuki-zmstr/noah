# Language Toggle Feature

This document describes the language toggle feature that allows users to switch between English and Japanese in the Noah reading assistant application.

## Overview

The language toggle feature provides:

- A button in the header to switch between English (🇺🇸) and Japanese (🇯🇵)
- Persistent language preference stored in localStorage
- Localized UI text based on the selected language
- Language information sent to the backend with user messages

## Components

### LanguageToggle Component

- **Location**: `src/components/LanguageToggle.vue`
- **Purpose**: Renders the language toggle button
- **Features**:
  - Shows current language flag and label
  - Toggles between English and Japanese on click
  - Provides hover tooltips

### Language Store

- **Location**: `src/stores/language.ts`
- **Purpose**: Manages language state and persistence
- **Features**:
  - Reactive language state
  - localStorage persistence
  - Computed properties for language checks and labels

## Usage

### In Components

```vue
<script setup lang="ts">
import { useLanguageStore } from "@/stores/language";

const languageStore = useLanguageStore();
</script>

<template>
  <div>
    <!-- Use store directly for reactivity -->
    <p v-if="languageStore.isEnglish">Hello!</p>
    <p v-else>こんにちは！</p>

    <!-- Or use computed properties -->
    <p>{{ languageStore.languageLabel }}</p>
  </div>
</template>
```

### Language-Aware Text

The following UI elements are localized:

- Welcome messages
- Input placeholders
- Button labels
- Connection status
- Navigation links
- Preferences page content

## Backend Integration

When sending messages via WebSocket, the current language is included in the metadata:

```typescript
sendWebSocketMessage(message, sessionId, {
  language: languageStore.currentLanguage,
});
```

This allows the backend to:

- Provide responses in the appropriate language
- Store language preferences in user profiles
- Adapt recommendations based on language preference

## Testing

Tests are provided for both the component and store:

- `src/components/__tests__/LanguageToggle.test.ts`
- `src/stores/__tests__/language.test.ts`

Run tests with:

```bash
npm run test
```

## Future Enhancements

Potential improvements:

- Add more languages
- Implement full i18n with translation files
- Add language-specific content recommendations
- Support for mixed-language conversations
