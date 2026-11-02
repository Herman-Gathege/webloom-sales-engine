/**
 * The Lead contract for Sprint 1.
 *
 * This is the frontend's copy of `docs/delivery/sprint-1-lead-contract.md`. That
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
export type ComplianceStatus = "eligible" | "needs_review" | "blocked" | "invalid";
export type DataQualityStatus = "complete" | "incomplete" | "invalid";
export type Channel = "email" | "sms" | "whatsapp";

export interface ChannelComplianceResult {
  channel: Channel;
  status: ComplianceStatus;
  technical_available: boolean;
  decision_current: boolean;
  reason_codes: string[];
  explanation: string;
}

export interface LeadCompliance {
  status: ComplianceStatus;
  data_quality_status: DataQualityStatus;
  reason_codes: string[];
  explanation: string;
  eligible_channels: Channel[];
  suppressed_channels: Channel[];
  channel_results: ChannelComplianceResult[];
  outreach_ready: boolean;
  evaluated_at: string;
  rule_version: string;
}

export interface Lead {
  /** UUID. */
  id: string;
  business_name: string;
  /** Free text in Sprint 1; normalised into a controlled vocabulary later. */
  sector: string | null;
  area: string | null;
  /** E.164, e.g. "+254709709000". */
  phone: string | null;
  /** Lower-case contact email, when research captured one. */
  email: string | null;
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
  compliance: LeadCompliance;
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
  /** Structured, non-sensitive audit facts. */
  details: Record<string, unknown> | null;
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
  q?: string;
  sector?: string;
  area?: string;
  source?: string;
  website?: "yes" | "no";
  status?: LeadStatus;
  compliance_status?: ComplianceStatus;
  data_quality_status?: DataQualityStatus;
  provenance?: "available" | "missing" | "incomplete";
  outreach_ready?: boolean;
  has_suppression?: boolean;
  batch_id?: string;
  sort?: "newest" | "oldest" | "business_name" | "compliance_status";
}

export interface ImportBatchOption {
  id: string;
  filename: string;
  imported_at: string;
}

export interface LeadFilterOptions {
  sectors: string[];
  areas: string[];
  sources: string[];
  statuses: LeadStatus[];
  compliance_statuses: ComplianceStatus[];
  data_quality_statuses: DataQualityStatus[];
  import_batches: ImportBatchOption[];
}

/** GET /api/v1/leads/{id} */
export interface LeadDetail extends Lead {
  provenance: LeadProvenance | null;
  eligibility: ChannelEligibility[];
  suppressions: Suppression[];
  activity: Activity[];
}

export type ContactType = "unknown" | "generic_business" | "named_individual";

export interface LeadProvenance {
  import_batch_id: string | null;
  row_number: number | null;
  source_name: string | null;
  source_url: string | null;
  collection_date: string | null;
  collection_method: string | null;
  intended_purpose: string | null;
  contact_type: ContactType;
  contact_name: string | null;
}

export type EligibilityState = "needs_review" | "eligible";
export type EffectiveEligibilityState = EligibilityState | "suppressed";
export type LawfulBasis =
  | "consent"
  | "contract"
  | "legal_obligation"
  | "vital_interests"
  | "public_interest"
  | "legitimate_interests"
  | "research_statistics";

export interface ChannelEligibility {
  channel: Channel;
  state: EligibilityState;
  effective_state: EffectiveEligibilityState;
  technical_available: boolean;
  lawful_basis: LawfulBasis | null;
  evidence_summary: string | null;
  evidence_source: string | null;
  intended_purpose: string | null;
  contact_context: string | null;
  reviewer: string | null;
  reviewed_at: string | null;
  rationale: string | null;
}

export type SuppressionScope = "all_marketing" | Channel;
export type SuppressionReason = "opt_out" | "objection" | "manual_restriction";

export interface Suppression {
  id: string;
  contact_kind: "phone" | "email";
  scope: SuppressionScope;
  reason: SuppressionReason;
  source: string;
  recorded_by: string;
  note: string | null;
  created_at: string;
}

export interface EligibilityReviewInput {
  state: EligibilityState;
  lawful_basis: LawfulBasis | null;
  evidence_summary: string | null;
  evidence_source: string | null;
  intended_purpose: string | null;
  contact_context: string | null;
  reviewer: string;
  rationale: string;
}

export interface SuppressionInput {
  scope: SuppressionScope;
  reason: SuppressionReason;
  source: string;
  recorded_by: string;
  note: string | null;
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

/** One row the importer refused, and the reason a person reads. */
export interface RefusedRow {
  /** Physical line in the file, with the header as line 1. */
  row: number;
  business_name: string;
  code: string;
  reason: string;
}

/** A value the importer kept but could not classify. Never reduces `accepted`. */
export interface RowWarning {
  row: number;
  field: string;
  value: string;
  code: string;
  message: string;
}

/** POST /api/v1/leads/import — what happened to the upload, row by row. */
export interface ImportSummary {
  filename: string;
  batch_id: string;
  row_count: number;
  accepted: number;
  created: number;
  rejected: number;
  matched: number;
  duplicates: number;
  eligible: number;
  needs_review: number;
  blocked: number;
  invalid: number;
  provenance_incomplete: number;
  requiring_review: number;
  rejected_rows: RefusedRow[];
  review_rows: ImportReviewRow[];
  warnings: RowWarning[];
}

export interface ImportReviewRow {
  row: number;
  business_name: string;
  compliance_status: Exclude<ComplianceStatus, "eligible">;
  reason_codes: string[];
  explanation: string;
}

export interface OutreachCheckResult {
  lead_id: string;
  channel: Channel;
  allowed: boolean;
  compliance_status: ComplianceStatus;
  reason_codes: string[];
  explanation: string;
  evaluated_at: string;
}

export interface OutreachCheckResponse {
  channel: Channel;
  results: OutreachCheckResult[];
}
