import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Unified API URL - All APIs now run on port 3000
const API_URL = process.env.API_URL || 'http://localhost:3000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Load .env from root directory (Chanakya/)
  envDir: path.resolve(__dirname, '../../'),
  server: {
    host: true,
    proxy: {
      // Dashboard API endpoints - proxied to unified server
      '/api/dashboard': {
        target: API_URL,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/dashboard/, '/api')
      },
      // All other /api calls go directly to unified server
      '/api': {
        target: API_URL,
        changeOrigin: true
      },
      // Health check
      '/health': {
        target: API_URL,
        changeOrigin: true
      }
    }
  }
})
