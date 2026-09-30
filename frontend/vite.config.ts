import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

// Dev-прокси: фронтенд ходит на относительные /api и /ws,
// а Vite перенаправляет их на FastAPI (VITE_PROXY_TARGET, по умолчанию :8000).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const target = env.VITE_PROXY_TARGET || 'http://localhost:8000';
  return {
    plugins: [react()],
    resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
    server: {
      port: 3000,
      proxy: {
        '/api': { target, changeOrigin: true },
        '/ws': { target: target.replace(/^http/, 'ws'), ws: true, changeOrigin: true },
      },
    },
    preview: { port: 3000 },
    worker: { format: 'es' },
    build: {
      target: 'es2020',
      chunkSizeWarningLimit: 4000,
      rollupOptions: {
        output: {
          manualChunks: {
            react: ['react', 'react-dom'],
            charts: ['lightweight-charts'],
            motion: ['framer-motion'],
          },
        },
      },
    },
  };
});
