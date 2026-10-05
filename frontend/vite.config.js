import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      '/api': {
        // host ต้องตรงกับ GOOGLE_REDIRECT_URI ใน backend/.env (cookie ผูกกับ host)
        target: 'http://127.0.0.1:8002',
        changeOrigin: true,
      },
    },
  },
})
