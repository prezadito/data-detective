import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { visualizer } from 'rollup-plugin-visualizer'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // Bundle analyzer - generates stats.html after build
    visualizer({
      open: false, // Set to true to auto-open after build
      gzipSize: true,
      brotliSize: true,
      filename: 'dist/stats.html',
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    // Manual chunk splitting for better caching and parallel loading
    rollupOptions: {
      output: {
        manualChunks: {
          // React ecosystem (core dependencies, rarely change)
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],

          // Form libraries (used across multiple forms)
          'vendor-forms': ['react-hook-form', '@hookform/resolvers', 'zod'],

          // Charts library (heavy, only used in teacher analytics)
          'vendor-charts': ['recharts'],

          // SQL.js (heavy WebAssembly, only used in practice mode)
          'vendor-sql': ['sql.js'],
        },
      },
    },
    // Increase chunk size warning limit for sql.js (large WASM file)
    chunkSizeWarningLimit: 2000,
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
