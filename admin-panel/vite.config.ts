import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    target: 'es2020',
    cssCodeSplit: true,
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined;
          if (id.match(/node_modules\/(react|react-dom|react-router|react-router-dom|scheduler)\b/)) {
            return 'react-vendor';
          }
          if (id.match(/node_modules\/(@tanstack\/react-query|axios|zustand)\b/)) {
            return 'data-vendor';
          }
          if (id.includes('node_modules/react-hot-toast')) {
            return 'ui-vendor';
          }
          return undefined;
        },
      },
    },
  },
  server: {
    port: 5173,
  },
});
