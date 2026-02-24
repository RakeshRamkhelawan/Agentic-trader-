import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

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
      '/api': {
        target: 'http://localhost:8003',  // Docker backend API
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://localhost:8003',
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
