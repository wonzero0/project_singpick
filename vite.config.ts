import { defineConfig } from 'vite';
import path from 'path';
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  base: './',
  plugins: [
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  assetsInclude: ['**/*.svg', '**/*.csv'],
  server: {
    host: '0.0.0.0', // 갤탭 접속 허용
    port: 5173,
    proxy: {
      '/library': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/kiosk': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/led': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
});