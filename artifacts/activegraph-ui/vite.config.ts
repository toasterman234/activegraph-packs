import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

// PORT and BASE_PATH are injected by Replit's artifact system. Off-platform
// (e.g. a plain GitHub checkout) they fall back to sane defaults so that
// `pnpm --filter @workspace/activegraph-ui run dev` just works with no setup.
const port = Number(process.env.PORT ?? "5173");

if (Number.isNaN(port) || port <= 0) {
  throw new Error(`Invalid PORT value: "${process.env.PORT}"`);
}

const basePath = process.env.BASE_PATH ?? "/";

// On Replit the platform path-routes /api to the API server, so Vite needs no
// proxy. Off-platform the API server runs on its own port, so proxy /api to it.
const onReplit = process.env.REPL_ID !== undefined;
const apiProxyTarget = process.env.API_PROXY_TARGET ?? "http://localhost:5000";

// Replit editor-only plugins. Loaded only during dev on Replit; in a plain
// GitHub checkout none of them are active, keeping the off-platform build clean.
const replitDevPlugins =
  !onReplit || process.env.NODE_ENV === "production"
    ? []
    : await Promise.all([
        import("@replit/vite-plugin-runtime-error-modal").then((m) =>
          m.default(),
        ),
        import("@replit/vite-plugin-cartographer").then((m) =>
          m.cartographer({
            root: path.resolve(import.meta.dirname, "../.."),
          }),
        ),
        import("@replit/vite-plugin-dev-banner").then((m) => m.devBanner()),
      ]).catch(() => []);

export default defineConfig({
  base: basePath,
  plugins: [react(), tailwindcss(), ...replitDevPlugins],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "src"),
    },
    dedupe: ["react", "react-dom"],
  },
  root: path.resolve(import.meta.dirname),
  build: {
    outDir: path.resolve(import.meta.dirname, "dist/public"),
    emptyOutDir: true,
  },
  server: {
    port,
    strictPort: true,
    host: "0.0.0.0",
    allowedHosts: true,
    fs: {
      strict: true,
    },
    // Off-platform only: forward API calls to the local API server.
    ...(onReplit
      ? {}
      : {
          proxy: {
            "/api": { target: apiProxyTarget, changeOrigin: true },
          },
        }),
  },
  preview: {
    port,
    host: "0.0.0.0",
    allowedHosts: true,
  },
});
