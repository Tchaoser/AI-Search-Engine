import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  // Force consistent ports across all machines
  server: {
    host: true,        // same as --host 0.0.0.0
    port: 5173,
    strictPort: true,  // fail instead of picking a random port
  },

  preview: {
    host: true,
    port: 5173,
    strictPort: true,
  },
})
