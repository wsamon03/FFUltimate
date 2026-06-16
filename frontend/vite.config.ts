import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    proxy: {
      '/api/stats': 'http://localhost:8002',
      '/api': 'http://localhost:8001',
      '/auth/login': 'http://localhost:8001',
      '/auth/register': 'http://localhost:8001',
      '/auth/refresh': 'http://localhost:8001',
      '/auth/logout': 'http://localhost:8001',
      '/auth/me': 'http://localhost:8001',
    },
  },
})
