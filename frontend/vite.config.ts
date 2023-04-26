import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue(), vueJsx()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  // 指示index.html中使用相对路径寻址
  base:'./',
  // 禁止变动描述符、类名称
  esbuild: {
    minifyIdentifiers: false,
    keepNames: true,
  },
})
