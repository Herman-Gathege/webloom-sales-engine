/**
 * The only module that knows how leads are fetched.
 *
 * It calls the real API first. If the API is not up yet — which it is not,
 * until Sharon's block lands — it falls back to bundled fixtures and says so
 * on screen. So the shell is demoable today, it switches to real data by
 * itself the moment the endpoints answer, and nothing fails silently.
 */

import { sampleLeadDetails, sampleLeads } from "./fixtures";
import type { LeadDetail, LeadListParams, LeadListResponse, Loaded } from "./types";

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
