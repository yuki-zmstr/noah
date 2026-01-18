/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_SOCKET_URL: string
  readonly VITE_AWS_REGION: string
  readonly VITE_COGNITO_USER_POOL_ID: string
  readonly VITE_COGNITO_CLIENT_ID: string
  readonly VITE_COGNITO_IDENTITY_POOL_ID: string
  readonly VITE_API_ENDPOINT: string
  readonly VITE_ENABLE_DISCOVERY_MODE: string
  readonly VITE_ENABLE_MULTILINGUAL: string
  readonly VITE_ENABLE_PURCHASE_LINKS: string
  readonly VITE_DEFAULT_LANGUAGE: string
  readonly VITE_MAX_MESSAGE_LENGTH: string
  readonly VITE_TYPING_INDICATOR_DELAY: string
  readonly BASE_URL: string
  readonly NODE_ENV: string
  readonly MODE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}