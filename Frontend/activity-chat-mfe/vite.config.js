import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import federation from '@originjs/vite-plugin-federation'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(__dirname, '../../'), '')
  const API_URL = env.VITE_API_URL || env.API_URL || 'http://localhost:3000'

  return {
    plugins: [
      react(),
      federation({
        name: 'activity_chat_mfe',
        filename: 'remoteEntry.js',
        exposes: {
          './ActivityChatRoutes': './src/ActivityChatRoutes.jsx',
        },
        shared: ['react', 'react-dom', 'react-router-dom', 'axios']
      })
    ],
    envDir: path.resolve(__dirname, '../../'),
    server: {
      host: true,
      port: 5177,
      cors: true,
      proxy: {
        '/api': {
          target: API_URL,
          changeOrigin: true
        }
      }
    },
    preview: {
      host: true,
      port: 5177,
      cors: true
    },
    build: {
      modulePreload: false,
      target: 'esnext',
      minify: false,
      cssCodeSplit: false
    }
  }
})
