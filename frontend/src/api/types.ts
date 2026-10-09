/**
 * The Lead contract for Epic 1.
 *
 * This is the frontend's copy of `docs/delivery/epic-1-lead-contract.md`. That
 * document is the source of truth — if a field changes, change both in the same
 * pull request. Field names are snake_case so there is never a mapping layer to
 * get out of step with FastAPI.
 */

/** Scope spec §5.1: the funnel stages, then the ways a lead ends. */
export const LEAD_STATUSES = [
  "new",
  "contacted",
  "replied",
  "qualified",
  "handed_off",
  "proposal",
  "won",
  "lost",
  "no_response",
  "not_interested",
  "opted_out",
] as const;

export type LeadStatus = (typeof LEAD_STATUSES)[number];

export interface Lead {
  /** UUID. */
  id: string;
  business_name: string;
  /** Free text in Epic 1; normalised into a controlled vocabulary later. */
  sector: string | null;
  area: string | null;
  /** E.164, e.g. "+254709709000". */
  phone: string | null;
  whatsapp_capable: boolean;
  /** The raw research string, kept verbatim. Free text. */
  website_status: string | null;
  has_website: boolean;
  /** Where the lead came from, e.g. "google_maps". */
  source: string;
  status: LeadStatus;
  /** ISO 8601, UTC. */
  created_at: string;
  updated_at: string;
}

export interface Activity {
  id: string;
  lead_id: string;
  /** e.g. "lead.created". */
  type: string;
  /** "system" until auth exists. */
  actor: string;
  /** Human-readable one-liner, derived on the server. */
  summary: string;
  /** ISO 8601, UTC. */
  created_at: string;
}

/** GET /api/v1/leads */
export interface LeadListResponse {
  items: Lead[];
  total: number;
  limit: number;
  offset: number;
}

export interface LeadListParams {
  limit?: number;
  offset?: number;
}

/** GET /api/v1/leads/{id} */
export interface LeadDetail extends Lead {
  activity: Activity[];
}

/**
 * Where the data on screen came from. "sample" means the API could not be
 * reached and the UI fell back to bundled fixtures — so the screens always
 * run, and the demo never silently lies about which one you are looking at.
 */
export type DataSource = "api" | "sample";

export interface Loaded<T> {
  data: T;
  source: DataSource;
  /** Why we fell back to sample data. Shown in the banner when source is "sample". */
  reason?: string;
}
