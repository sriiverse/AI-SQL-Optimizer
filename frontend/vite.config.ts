/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/tests/setup.ts',
  },
  server: {
    allowedHosts: true,
    proxy: {
      '/analyze': 'http://localhost:8000',
      '/generate-sql': 'http://localhost:8000',
    }
  }
})
