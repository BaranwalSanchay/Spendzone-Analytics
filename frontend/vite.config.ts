import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    // Docker Desktop's bind mounts (notably on Windows/macOS) don't forward native
    // filesystem events into the container, so HMR silently stops working unless the
    // watcher polls instead. Only enabled inside the Docker Compose dev container
    // (DOCKER=true, set in docker-compose.yml) — native/non-Docker dev is unaffected.
    watch: process.env.DOCKER === "true" ? { usePolling: true } : undefined,
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  assetsInclude: ['**/*.pdf'],
}));
