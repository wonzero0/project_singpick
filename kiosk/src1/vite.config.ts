import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

const backendTarget = process.env.VITE_BACKEND_ORIGIN || 'http://localhost:8000'

const apiProxy: Record<string, any> = [
  '/library', '/kiosk', '/led', '/users', 
  '/songs', '/booth', '/mr_files', '/session',
].reduce((proxy, route) => {
  proxy[route] = { target: backendTarget, changeOrigin: true }
  return proxy
}, {} as Record<string, any>)

export default defineConfig({
  root: __dirname,
  plugins: [react(), tailwindcss()],

  build: {
    rollupOptions: {
      input: path.resolve(__dirname, 'index.html'),
    },
    sourcemap: true, 
  },

  envDir: path.resolve(__dirname, '../..'),
  
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: apiProxy,
  },
})