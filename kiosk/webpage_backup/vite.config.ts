import { defineConfig } from 'vite';
import path from 'path';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

/**
 * 피그마 에셋을 src/assets 경로에서 찾아주는 커스텀 플러그인
 */
function figmaAssetResolver() {
  return {
    name: 'figma-asset-resolver',
    resolveId(id: string) {
      if (id.startsWith('figma:asset/')) {
        const filename = id.replace('figma:asset/', '');
        return path.resolve(__dirname, 'src/assets', filename);
      }
      return null;
    },
  };
}

export default defineConfig({
  // 여기에서 any[]로 강제 캐스팅하여 타입 분석 깊이 제한을 회피합니다.
  plugins: [
    figmaAssetResolver(),
    react(),
    tailwindcss(),
  ] as any[], 
  
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
  
  assetsInclude: [
    '**/*.svg', 
    '**/*.csv'
  ],
});