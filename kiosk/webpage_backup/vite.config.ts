import { defineConfig } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

function figmaAssetResolver() {
  return {
    name: 'figma-asset-resolver',
    resolveId(id: string) {
      if (id.startsWith('figma:asset/')) {
        const filename = id.replace('figma:asset/', '')
        return path.resolve(__dirname, 'src/assets', filename)
      }
    },
  }
}

export default defineConfig({
  plugins: [
    figmaAssetResolver(),
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      // @를 src 폴더로 매핑
      '@': path.resolve(__dirname, './src'),
    },
  },
  // 서버 설정 추가: 휴대폰 접속을 위해 host 추가
  server: {
    host: '0.0.0.0', 
  },
  // 파일 타입 지원
  assetsInclude: ['**/*.svg', '**/*.csv'],
})