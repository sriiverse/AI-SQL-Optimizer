import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: true,
    proxy: {
      '/analyze': 'http://localhost:8000',
      '/generate-sql': 'http://localhost:8000',
    }
  }
})
