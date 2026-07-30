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

  // Resolve microfrontend ports and URLs from environment
  const DASHBOARD_PORT = env.VITE_DASHBOARD_MFE_PORT || '5174'
  const QNA_PORT = env.VITE_QNA_CHAT_MFE_PORT || '5175'
  const DISCUSS_PORT = env.VITE_DISCUSS_MFE_PORT || '5176'
  const ACTIVITY_PORT = env.VITE_ACTIVITY_CHAT_MFE_PORT || '5177'
  const MODULE_PORT = env.VITE_MODULE_CHAT_MFE_PORT || '5178'

  const DASHBOARD_URL = env.VITE_DASHBOARD_MFE_URL || `http://localhost:${DASHBOARD_PORT}`
  const QNA_URL = env.VITE_QNA_CHAT_MFE_URL || `http://localhost:${QNA_PORT}`
  const DISCUSS_URL = env.VITE_DISCUSS_MFE_URL || `http://localhost:${DISCUSS_PORT}`
  const ACTIVITY_URL = env.VITE_ACTIVITY_CHAT_MFE_URL || `http://localhost:${ACTIVITY_PORT}`
  const MODULE_URL = env.VITE_MODULE_CHAT_MFE_URL || `http://localhost:${MODULE_PORT}`

  return {
    plugins: [
      react(),
      federation({
        name: 'host',
        remotes: {
          dashboard_mfe: `${DASHBOARD_URL}/assets/remoteEntry.js`,
          qna_chat_mfe: `${QNA_URL}/assets/remoteEntry.js`,
          activity_chat_mfe: `${ACTIVITY_URL}/assets/remoteEntry.js`,
          module_chat_mfe: `${MODULE_URL}/assets/remoteEntry.js`,
          discuss_mfe: `${DISCUSS_URL}/assets/remoteEntry.js`,
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
