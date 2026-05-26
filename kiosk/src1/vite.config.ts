import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

const backendTarget =
  process.env.VITE_BACKEND_ORIGIN || 'http://localhost:8000'

const apiProxy: Record<string, { target: string; changeOrigin: boolean }> = [
  '/library',
  '/kiosk',
  '/led',
  '/users',
  '/songs',
  '/booth',
  '/mr_files',
].reduce((proxy, route) => {
  proxy[route] = {
    target: backendTarget,
    changeOrigin: true,
  }
  return proxy
}, {} as Record<string, { target: string; changeOrigin: boolean }>)

export default defineConfig({
  envDir: path.resolve(__dirname, '../..'),
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: apiProxy,
  },
})
