import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          // Separate ECharts into its own chunk
          'echarts': ['echarts/core', 'echarts/charts', 'echarts/components', 'echarts/renderers'],
          // Separate Vue ecosystem
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          // Separate other vendor libraries
          'vendor': ['axios']
        }
      }
    },
    // Use esbuild for minification (built into Vite)
    minify: 'esbuild'
  }
})
