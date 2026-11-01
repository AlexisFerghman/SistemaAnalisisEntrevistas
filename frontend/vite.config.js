import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    proxy: {
      '/health': 'http://api:8000',
      '/api': 'http://api:8000',
    },
  },
})
