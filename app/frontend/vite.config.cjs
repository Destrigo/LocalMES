const { defineConfig } = require('vite')
const react = require('@vitejs/plugin-react')
const tailwindcss = require('@tailwindcss/vite')

module.exports = defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/static': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
