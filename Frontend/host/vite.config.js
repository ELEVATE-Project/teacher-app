import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import federation from '@originjs/vite-plugin-federation'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file from root directory (Chanakya/)
  const env = loadEnv(mode, path.resolve(__dirname, '../../'), '')
  
  // Unified API URL - defaults to port 3000 or the config port
  const API_URL = env.VITE_API_URL || env.API_URL || 'http://localhost:3000'
  const frontendPort = parseInt(env.FRONTEND_PORT || env.PORT || '5173')

  return {
    plugins: [
      react(),
      federation({
        name: 'host',
        remotes: {
          dashboard_mfe: 'http://localhost:5174/assets/remoteEntry.js',
          qna_chat_mfe: 'http://localhost:5175/assets/remoteEntry.js',
          activity_chat_mfe: 'http://localhost:5177/assets/remoteEntry.js',
          module_chat_mfe: 'http://localhost:5178/assets/remoteEntry.js',
          discuss_mfe: 'http://localhost:5176/assets/remoteEntry.js',
        },
        shared: ['react', 'react-dom', 'react-router-dom', 'axios']
      })
    ],
    envDir: path.resolve(__dirname, '../../'),
    server: {
      host: true,
      port: frontendPort,
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
    },
    build: {
      modulePreload: false,
      target: 'esnext',
      minify: false,
      cssCodeSplit: false
    }
  }
})
