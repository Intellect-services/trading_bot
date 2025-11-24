import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: parseInt(process.env.VITE_PORT || process.env.PORT || '5173', 10),
    host: true,
    strictPort: false, // Allow using alternative port if specified port is busy
  },
})
