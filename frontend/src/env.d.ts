/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the control plane. Empty means same origin (the Vite dev proxy). */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
