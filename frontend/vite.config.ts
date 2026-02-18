import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// https://vite.dev/config/
export default defineConfig({
  base: './',
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      // Proxy API calls to the backend container
      '/api': {
        target: 'http://api-server:8001',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://api-server:8001',
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
