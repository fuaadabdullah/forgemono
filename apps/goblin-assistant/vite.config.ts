import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      '@tanstack/react-query',
      'react-router-dom',
      'zustand',
      'axios'
    ],
  },
  server: {
    port: 3000,
    host: true,
    open: false,
  },
  build: {
    sourcemap: false,
    target: 'esnext',
    rollupOptions: {
      output: {
        // Explicit vendor chunking for better long-term caching & smaller initial index.* bundle.
        manualChunks: {
          react: ['react', 'react-dom', 'react-router-dom'],
          query: ['@tanstack/react-query'],
          state: ['zustand'],
            net: ['axios'],
          icons: ['lucide-react']
        }
      }
    }
  },
})
