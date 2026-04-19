import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Allows "@/components/..." imports throughout the codebase
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    // Allow binding to a network IP so the app is reachable from other devices
    host: true,
    port: 5173,
  },
});
