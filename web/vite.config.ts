import { defineConfig } from 'vite'

// https://vitejs.dev/config/
export default defineConfig(async () => {
  const { default: react } = await import('@vitejs/plugin-react')
  return {
    plugins: [react()],
    resolve: {
      alias: {
        // Optional: alias for auth client if needed, but relative import should suffice
      }
    },
    define: {
      // No env bundling; API_BASE_URL set via index.html script
    }
  }
})