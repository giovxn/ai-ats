import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The frontend calls /api/...; Vite forwards those requests to the FastAPI backend.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
