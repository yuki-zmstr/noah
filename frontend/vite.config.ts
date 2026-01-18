import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  // Explicitly define env variables to ensure they're embedded in the build
  define: {
    'import.meta.env.VITE_AWS_REGION': JSON.stringify(process.env.VITE_AWS_REGION),
    'import.meta.env.VITE_COGNITO_USER_POOL_ID': JSON.stringify(process.env.VITE_COGNITO_USER_POOL_ID),
    'import.meta.env.VITE_COGNITO_CLIENT_ID': JSON.stringify(process.env.VITE_COGNITO_CLIENT_ID),
    'import.meta.env.VITE_COGNITO_IDENTITY_POOL_ID': JSON.stringify(process.env.VITE_COGNITO_IDENTITY_POOL_ID),
    'import.meta.env.VITE_API_ENDPOINT': JSON.stringify(process.env.VITE_API_ENDPOINT),
    'import.meta.env.VITE_API_BASE_URL': JSON.stringify(process.env.VITE_API_BASE_URL),
    'import.meta.env.VITE_ENABLE_DISCOVERY_MODE': JSON.stringify(process.env.VITE_ENABLE_DISCOVERY_MODE),
    'import.meta.env.VITE_ENABLE_MULTILINGUAL': JSON.stringify(process.env.VITE_ENABLE_MULTILINGUAL),
    'import.meta.env.VITE_ENABLE_PURCHASE_LINKS': JSON.stringify(process.env.VITE_ENABLE_PURCHASE_LINKS),
    'import.meta.env.VITE_DEFAULT_LANGUAGE': JSON.stringify(process.env.VITE_DEFAULT_LANGUAGE),
    'import.meta.env.VITE_MAX_MESSAGE_LENGTH': JSON.stringify(process.env.VITE_MAX_MESSAGE_LENGTH),
    'import.meta.env.VITE_TYPING_INDICATOR_DELAY': JSON.stringify(process.env.VITE_TYPING_INDICATOR_DELAY),
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'https://api-noah.com',
        changeOrigin: true,
      },
      '/socket.io': {
        target: 'https://api-noah.com',
        ws: true,
      },
    },
  },
})