import { defineConfig } from "vite";
import path from "path";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const backendTarget =
  process.env.VITE_BACKEND_ORIGIN || "http://localhost:8000";

const apiProxy: Record<string, { target: string; changeOrigin: boolean }> = [
  "/library",
  "/kiosk",
  "/led",
  "/users",
  "/songs",
  "/booth",
  "/mr_files",
].reduce((proxy, path) => {
  proxy[path] = {
    target: backendTarget,
    changeOrigin: true,
  };
  return proxy;
}, {} as Record<string, { target: string; changeOrigin: boolean }>);

function figmaAssetResolver() {
  return {
    name: "figma-asset-resolver",

    resolveId(id: string) {

      if (id.startsWith("figma:asset/")) {

        const filename = id.replace(
          "figma:asset/",
          ""
        );

        return path.resolve(
          __dirname,
          "src1/assets",
          filename
        );
      }
    },
  };
}

export default defineConfig({
 
  plugins: [
    figmaAssetResolver(),
    react(),
    tailwindcss(),
  ],

  resolve: {
    alias: {

      // 🔥 src1 기준
      "@": path.resolve(__dirname, "./src1"),
    },
  },

  assetsInclude: [
    "**/*.svg",
    "**/*.csv",
  ],

  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: apiProxy,
  },
});
