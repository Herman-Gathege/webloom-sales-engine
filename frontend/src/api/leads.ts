/**
 * The only module that knows how leads are fetched.
 *
 * It calls the real API first. If the API is not up yet — which it is not,
 * until Sharon's block lands — it falls back to bundled fixtures and says so
 * on screen. So the shell is demoable today, it switches to real data by
 * itself the moment the endpoints answer, and nothing fails silently.
 */

import { sampleLeadDetails, sampleLeads } from "./fixtures";
import type {
  ImportSummary,
  LeadDetail,
  LeadListParams,
  LeadListResponse,
  Loaded,
} from "./types";

/** The dev server proxies /api to the FastAPI service (see vite.config.ts). */
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "/api/v1").replace(/\/+$/, "");

/** Set VITE_USE_MOCK=1 to skip the API entirely, e.g. with no backend running. */
const FORCE_SAMPLE = import.meta.env.VITE_USE_MOCK === "1";

const REQUEST_TIMEOUT_MS = 4000;

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new ApiError(`The API answered ${response.status} for ${path}.`, response.status);
    }
    return (await response.json()) as T;
  } catch (cause) {
    if (cause instanceof ApiError) throw cause;
    throw new ApiError(`Could not reach the API at ${API_BASE_URL}.`, 0);
  } finally {
    clearTimeout(timer);
  }
}

export async function listLeads(
  params: LeadListParams = {},
): Promise<Loaded<LeadListResponse>> {
  const limit = params.limit ?? 50;
  const offset = params.offset ?? 0;

  const fromSample = (reason?: string): Loaded<LeadListResponse> => ({
    source: "sample",
    reason,
    data: {
      items: sampleLeads.slice(offset, offset + limit),
      total: sampleLeads.length,
      limit,
      offset,
    },
  });

  if (FORCE_SAMPLE) return fromSample("VITE_USE_MOCK=1");

  try {
    return {
      source: "api",
      data: await request<LeadListResponse>(`/leads?limit=${limit}&offset=${offset}`),
    };
  } catch (cause) {
    return fromSample(cause instanceof Error ? cause.message : undefined);
  }
}

export async function getLead(id: string): Promise<Loaded<LeadDetail>> {
  const fromSample = (reason?: string): Loaded<LeadDetail> => {
    const found = sampleLeadDetails.find((lead) => lead.id === id);
    if (!found) throw new ApiError(`No lead with id ${id}.`, 404);
    return { source: "sample", reason, data: found };
  };

  if (FORCE_SAMPLE) return fromSample("VITE_USE_MOCK=1");

  try {
    return { source: "api", data: await request<LeadDetail>(`/leads/${encodeURIComponent(id)}`) };
  } catch (cause) {
    // A reachable API that answers 404 has answered us. Do not hide that behind
    // sample data — a missing lead is a real result and the UI should say so.
    if (cause instanceof ApiError && cause.status >= 400 && cause.status < 500) throw cause;
    return fromSample(cause instanceof Error ? cause.message : undefined);
  }
}

/**
 * Upload the researched CSV and get back what happened to every row.
 *
 * Uses XMLHttpRequest rather than fetch for one reason: it reports upload
 * progress, so the screen shows a real bar instead of a spinner that could mean
 * anything. `onProgress` is called with 0-100.
 *
 * This is deliberately not wrapped in the sample-data fallback. Pretending an
 * upload succeeded would be worse than failing.
 */
export function importLeads(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<ImportSummary> {
  return new Promise<ImportSummary>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE_URL}/leads/import`);
    xhr.setRequestHeader("Accept", "application/json");
    xhr.responseType = "text";
    xhr.timeout = 60_000;

    xhr.upload.onprogress = (event) => {
      if (onProgress && event.lengthComputable && event.total > 0) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText) as ImportSummary);
        } catch {
          reject(new ApiError("The API sent a response we could not read.", xhr.status));
        }
        return;
      }

      let detail = `The import failed (${xhr.status}).`;
      try {
        const parsed = JSON.parse(xhr.responseText) as { detail?: unknown };
        if (typeof parsed.detail === "string") detail = parsed.detail;
      } catch {
        // The body was not JSON; keep the generic message.
      }
      reject(new ApiError(detail, xhr.status));
    };

    xhr.onerror = () => reject(new ApiError("Could not reach the API.", 0));
    xhr.ontimeout = () => reject(new ApiError("The upload timed out.", 0));

    const body = new FormData();
    body.append("file", file);
    xhr.send(body);
  });
}

/**
 * The downloadable refusal report, built from the summary we already have.
 *
 * Deliberately not the API's `?format=csv` path: that re-runs the import, so
 * calling it after a successful upload would report every row as a duplicate.
 * This describes the import that actually happened, with no second request.
 */
export function rejectedRowsCsv(summary: ImportSummary): string {
  const cell = (value: string | number) => {
    const text = String(value);
    return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
  };

  const lines = [
    "row,business_name,code,reason",
    ...summary.rejected_rows.map((row) =>
      [row.row, row.business_name, row.code, row.reason].map(cell).join(","),
    ),
  ];

  return `${lines.join("\n")}\n`;
}
