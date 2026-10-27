/**
 * One place that knows where the API is, how to attach the token, and what a
 * failed request looks like. Everything else calls `apiRequest`.
 */

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "/api/v1"
).replace(/\/+$/, "");

const TOKEN_KEY = "wadi.token";
const REQUEST_TIMEOUT_MS = 10_000;

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

let unauthorizedHandler: (() => void) | null = null;

/** FastAPI sends either a string or a list of validation objects as `detail`. */
function detailMessage(detail: unknown): string | null {
  if (typeof detail === "string") return detail;
  if (!Array.isArray(detail)) return null;
  const messages = detail
    .map((item) =>
      item && typeof item === "object" && "msg" in item && typeof item.msg === "string"
        ? item.msg
        : null,
    )
    .filter((message): message is string => Boolean(message));
  return messages.length > 0 ? messages.join("; ") : null;
}

/** The auth provider registers this so an expired session returns to /login. */
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler;
}

export function getToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token);
    else window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    // A browser with storage disabled still works for the current page.
  }
}

export function clearToken(): void {
  setToken(null);
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers,
      signal: controller.signal,
    });

    if (!response.ok) {
      if (response.status === 401) {
        clearToken();
        unauthorizedHandler?.();
      }

      let detail = `Request failed (${response.status}).`;
      try {
        const body = (await response.json()) as { detail?: unknown };
        detail = detailMessage(body.detail) ?? detail;
      } catch {
        // Not JSON; keep the generic message.
      }
      throw new ApiError(detail, response.status);
    }

    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  } catch (cause) {
    if (cause instanceof ApiError) throw cause;
    throw new ApiError(`Could not reach the API at ${API_BASE_URL}.`, 0);
  } finally {
    clearTimeout(timer);
  }
}
