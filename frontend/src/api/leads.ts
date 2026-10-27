/**
 * The only module that knows how leads are fetched.
 *
 * It calls the real API first. If the API is not up yet — which it is not,
 * until Sharon's block lands — it falls back to bundled fixtures and says so
 * on screen. So the shell is demoable today, it switches to real data by
 * itself the moment the endpoints answer, and nothing fails silently.
 */

import { sampleLeadDetails, sampleLeads } from "./fixtures";
import { API_BASE_URL, ApiError, apiRequest, getToken } from "./client";
import type {
  Channel,
  EligibilityReviewInput,
  ImportSummary,
  LeadDetail,
  LeadFilterOptions,
  LeadListParams,
  LeadListResponse,
  Loaded,
  OutreachCheckResponse,
  SuppressionInput,
} from "./types";

// Existing imports of ApiError from this module keep working.
export { ApiError } from "./client";

/** Set VITE_USE_MOCK=1 to skip the API entirely, e.g. with no backend running. */
const FORCE_SAMPLE = import.meta.env.VITE_USE_MOCK === "1";

function sampleList(params: LeadListParams): LeadListResponse {
  const limit = params.limit ?? 50;
  const offset = params.offset ?? 0;
  const needle = params.q?.trim().toLowerCase() ?? "";
  let items = sampleLeads.filter((lead) => {
    const detail = sampleLeadDetails.find((entry) => entry.id === lead.id);
    if (params.sector && lead.sector !== params.sector) return false;
    if (params.area && lead.area !== params.area) return false;
    if (params.source && lead.source !== params.source) return false;
    if (params.website === "yes" && !lead.has_website) return false;
    if (params.website === "no" && lead.has_website) return false;
    if (params.status && lead.status !== params.status) return false;
    if (
      params.compliance_status &&
      lead.compliance.status !== params.compliance_status
    ) {
      return false;
    }
    if (
      params.data_quality_status &&
      lead.compliance.data_quality_status !== params.data_quality_status
    ) {
      return false;
    }
    if (params.outreach_ready !== undefined && lead.compliance.outreach_ready !== params.outreach_ready) {
      return false;
    }
    if (params.has_suppression !== undefined) {
      const hasSuppression = lead.compliance.suppressed_channels.length > 0;
      if (hasSuppression !== params.has_suppression) return false;
    }
    if (params.provenance === "missing" && detail?.provenance) return false;
    if (params.provenance !== "missing" && params.provenance && !detail?.provenance) {
      return false;
    }
    if (params.batch_id && detail?.provenance?.import_batch_id !== params.batch_id) {
      return false;
    }
    if (!needle) return true;
    return [lead.business_name, lead.phone ?? "", lead.email ?? "", lead.area ?? "", lead.sector ?? "", lead.source]
      .some((value) => value.toLowerCase().includes(needle));
  });

  if (params.sort === "oldest") {
    items = [...items].sort((a, b) => a.created_at.localeCompare(b.created_at));
  } else if (params.sort === "business_name") {
    items = [...items].sort((a, b) => a.business_name.localeCompare(b.business_name));
  } else if (params.sort === "compliance_status") {
    const order = { eligible: 0, needs_review: 1, blocked: 2, invalid: 3 };
    items = [...items].sort(
      (a, b) => order[a.compliance.status] - order[b.compliance.status],
    );
  }
  return {
    items: items.slice(offset, offset + limit),
    total: items.length,
    limit,
    offset,
  };
}

function leadQuery(params: LeadListParams): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, String(value));
    }
  }
  return query.toString();
}

async function mutate<T>(path: string, method: "POST" | "PUT", body: unknown): Promise<T> {
  return apiRequest<T>(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function listLeads(
  params: LeadListParams = {},
): Promise<Loaded<LeadListResponse>> {
  const fromSample = (reason?: string): Loaded<LeadListResponse> => ({
    source: "sample",
    reason,
    data: sampleList(params),
  });

  if (FORCE_SAMPLE) return fromSample("VITE_USE_MOCK=1");

  try {
    const query = leadQuery(params);
    return {
      source: "api",
      data: await apiRequest<LeadListResponse>(`/leads${query ? `?${query}` : ""}`),
    };
  } catch (cause) {
    return fromSample(cause instanceof Error ? cause.message : undefined);
  }
}

export async function getLeadFilterOptions(): Promise<Loaded<LeadFilterOptions>> {
  const fromSample = (reason?: string): Loaded<LeadFilterOptions> => ({
    source: "sample",
    reason,
    data: {
      sectors: [...new Set(sampleLeads.map((lead) => lead.sector).filter((value): value is string => Boolean(value)))].sort(),
      areas: [...new Set(sampleLeads.map((lead) => lead.area).filter((value): value is string => Boolean(value)))].sort(),
      sources: [...new Set(sampleLeads.map((lead) => lead.source))].sort(),
      statuses: [...new Set(sampleLeads.map((lead) => lead.status))],
      compliance_statuses: ["eligible", "needs_review", "blocked", "invalid"],
      data_quality_statuses: ["complete", "incomplete", "invalid"],
      import_batches: [
        {
          id: "30000000-0000-4000-8000-000000000001",
          filename: "synthetic-sample.csv",
          imported_at: "2026-09-23T09:00:00Z",
        },
      ],
    },
  });

  if (FORCE_SAMPLE) return fromSample("VITE_USE_MOCK=1");
  try {
    return {
      source: "api",
      data: await apiRequest<LeadFilterOptions>("/leads/filter-options"),
    };
  } catch (cause) {
    return fromSample(cause instanceof Error ? cause.message : undefined);
  }
}

export function checkOutreach(
  leadIds: string[],
  channel: "email" | "sms" | "whatsapp",
): Promise<OutreachCheckResponse> {
  return mutate<OutreachCheckResponse>("/leads/outreach-check", "POST", {
    lead_ids: leadIds,
    channel,
  });
}

export async function getLead(id: string): Promise<Loaded<LeadDetail>> {
  const fromSample = (reason?: string): Loaded<LeadDetail> => {
    const found = sampleLeadDetails.find((lead) => lead.id === id);
    if (!found) throw new ApiError(`No lead with id ${id}.`, 404);
    return { source: "sample", reason, data: found };
  };

  if (FORCE_SAMPLE) return fromSample("VITE_USE_MOCK=1");

  try {
    return { source: "api", data: await apiRequest<LeadDetail>(`/leads/${encodeURIComponent(id)}`) };
  } catch (cause) {
    // A reachable API that answers 404 has answered us. Do not hide that behind
    // sample data — a missing lead is a real result and the UI should say so.
    if (cause instanceof ApiError && cause.status >= 400 && cause.status < 500) throw cause;
    return fromSample(cause instanceof Error ? cause.message : undefined);
  }
}

export function reviewEligibility(
  id: string,
  channel: Channel,
  decision: EligibilityReviewInput,
): Promise<LeadDetail> {
  return mutate<LeadDetail>(
    `/leads/${encodeURIComponent(id)}/eligibility/${channel}`,
    "PUT",
    decision,
  );
}

export function recordSuppression(id: string, request: SuppressionInput): Promise<LeadDetail> {
  return mutate<LeadDetail>(`/leads/${encodeURIComponent(id)}/suppressions`, "POST", request);
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
    const token = getToken();
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
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
