import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Three pages: the story (/), /licenses and the 404 that Vercel serves for unknown paths.
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: { input: { main: 'index.html', licenses: 'licenses.html', notfound: '404.html' } },
  },
})
