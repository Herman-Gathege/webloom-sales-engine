/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the Sales Engine API. Defaults to "/api/v1" (proxied in dev). */
  readonly VITE_API_BASE_URL?: string;
  /** Set to "1" to always show bundled fixtures and never call the API. */
  readonly VITE_USE_MOCK?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
