import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

const backendTarget =
  process.env.VITE_BACKEND_ORIGIN || 'http://127.0.0.1:8000'

const apiProxy: Record<string, { target: string; changeOrigin: boolean }> = [
  '/library',
  '/kiosk',
  '/led',
  '/users',
  '/songs',
  '/booth',
  '/mr_files',
  '/session',
].reduce((proxy, route) => {
  proxy[route] = {
    target: backendTarget,
    changeOrigin: true,
  }
  return proxy
}, {} as Record<string, { target: string; changeOrigin: boolean }>)

export default defineConfig({
  root: __dirname,
  plugins: [react(), tailwindcss()],

  build: {
    rollupOptions: {
      input: path.resolve(__dirname, 'index.html'), // 🔥 핵심
    },
  },

  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: apiProxy,
  },
})
