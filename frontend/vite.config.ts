import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  return {
    plugins: [vue()],
    server: {
      host: '0.0.0.0',
      port: 3000,
      proxy: { '/api': { target: env.VITE_API_BASE_URL || 'http://localhost:8000', changeOrigin: true } },
    },
  }
})
