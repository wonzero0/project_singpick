import { defineConfig, loadEnv } from 'vite';
import path from 'path';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig(({ mode }) => {
  // 현재 실행 모드에 맞는 환경 변수를 로드
  const env = loadEnv(mode, process.cwd(), '');
  
  // 백엔드 주소: .env의 VITE_BACKEND_ORIGIN, 없으면 기본 로컬호스트
  const backendTarget = env.VITE_BACKEND_ORIGIN || 'http://localhost:8000';

  return {
    base: './',
    plugins: [
      react(),
      tailwindcss(),
    ] as any[], // 타입 에러 방지
    
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },

    server: {
      host: '0.0.0.0', // 외부 접속 허용
      port: 5173,
      proxy: {
        '/library': { target: backendTarget, changeOrigin: true },
        '/kiosk': { target: backendTarget, changeOrigin: true },
        '/led': { target: backendTarget, changeOrigin: true },
        '/users': { target: backendTarget, changeOrigin: true },
        '/songs': { target: backendTarget, changeOrigin: true },
        '/booth': { target: backendTarget, changeOrigin: true },
        '/mr_files': { target: backendTarget, changeOrigin: true },
      }
    }
  };
});