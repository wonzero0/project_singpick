import { defineConfig } from "vite";
import path from "path";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

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
    port: 5173,
  },
});