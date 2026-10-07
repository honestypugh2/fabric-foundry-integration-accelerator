import react from "@vitejs/plugin-react";
import { loadEnv, type Plugin } from "vite";
import { defineConfig } from "vitest/config";

/**
 * Adds a strict Content-Security-Policy to production builds only. The dev server injects an
 * inline React Refresh preamble that a strict policy would block.
 */
function contentSecurityPolicy(apiBaseUrl: string): Plugin {
  const connect = ["'self'", apiBaseUrl].filter(Boolean).join(" ");
  const policy = [
    "default-src 'self'",
    "img-src 'self' data:",
    "style-src 'self' 'unsafe-inline'",
    `connect-src ${connect}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join("; ");
  return {
    name: "ffia-content-security-policy",
    apply: "build",
    transformIndexHtml: () => [
      {
        tag: "meta",
        attrs: { "http-equiv": "Content-Security-Policy", content: policy },
        injectTo: "head-prepend",
      },
    ],
  };
}

function apiBaseUrl(mode: string): string {
  const env: Partial<Record<string, string>> = loadEnv(mode, process.cwd(), "VITE_");
  return env.VITE_API_BASE_URL ?? "";
}

export default defineConfig(({ mode }) => ({
  plugins: [react(), contentSecurityPolicy(apiBaseUrl(mode))],
  server: {
    port: 5173,
    strictPort: true,
    // Same-origin calls to the local control plane during development (`make run-api`).
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/ready": "http://127.0.0.1:8000",
    },
  },
  build: {
    sourcemap: true,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    css: false,
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/main.tsx", "src/test/**", "src/**/*.test.{ts,tsx}"],
      thresholds: {
        lines: 85,
        functions: 85,
        branches: 85,
        statements: 85,
      },
    },
  },
}));
