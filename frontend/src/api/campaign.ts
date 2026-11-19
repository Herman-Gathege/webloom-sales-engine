import { apiRequest } from "./client";

export type CampaignStatus = "draft" | "generated" | "archived";
export type CampaignChannel = "email" | "sms";
export type CampaignDecisionType = "automated_policy" | "human_review" | "none";

export interface CampaignSelectionContext {
  q?: string;
  sector?: string;
  area?: string;
  source?: string;
  website?: "yes" | "no" | "unknown";
  status?: string;
  compliance_status?: "eligible" | "needs_review" | "blocked" | "invalid";
  data_quality_status?: "complete" | "incomplete" | "invalid";
  provenance?: "available" | "missing" | "incomplete";
  outreach_ready?: boolean;
  exception_review?: boolean;
  has_suppression?: boolean;
  batch_id?: string;
}

export interface CampaignInput {
  name: string;
  goal: string;
  offer_id: string;
  template_id: string;
  channel: CampaignChannel;
  lead_ids: string[];
  selection_context: CampaignSelectionContext;
}

export interface CampaignPreviewLead {
  lead_id: string;
  business_name: string;
  sector: string | null;
  area: string | null;
  source: string;
  website_presence: "has_website" | "no_website" | "unknown";
  decision_type: CampaignDecisionType;
  explanation: string;
  policy_id: string | null;
  policy_version: string | null;
  technical_available: boolean;
  research_date: string | null;
  research_stale: boolean;
}

export interface CampaignSkip {
  lead_id: string;
  business_name: string;
  code: string;
  label: string;
  explanation: string;
  reason_codes: string[];
}

export interface CampaignPreview {
  eligible_count: number;
  skipped_count: number;
  eligible: CampaignPreviewLead[];
  skipped: CampaignSkip[];
  reason_counts: Record<string, number>;
}

export interface CampaignSummary {
  id: string;
  name: string;
  goal: string;
  channel: CampaignChannel;
  owner_id: string;
  owner_email: string;
  offer_id: string;
  offer_name: string;
  template_id: string;
  template_name: string;
  selected_count: number;
  draft_count: number;
  skip_count: number;
  status: CampaignStatus;
  created_at: string;
  updated_at: string;
  last_activity_at: string;
  generated_at: string | null;
  archived_at: string | null;
  archived_by_email: string | null;
}

export interface CampaignDraft {
  id: string;
  lead_id: string;
  business_name: string;
  sector: string | null;
  area: string | null;
  channel: CampaignChannel;
  state: "draft";
  rendered_body: string;
  sms_encoding: string | null;
  sms_characters: number | null;
  sms_units: number | null;
  sms_segments: number | null;
  eligibility_snapshot: Record<string, unknown>;
  template_snapshot: Record<string, unknown>;
  offer_snapshot: Record<string, unknown>;
  generated_at: string;
  research_date: string | null;
  research_stale: boolean;
}

export interface CampaignDetail extends CampaignSummary {
  offer_snapshot: Record<string, unknown>;
  template_snapshot: Record<string, unknown>;
  input_fingerprint: string;
  selection_context: CampaignSelectionContext;
  selected_lead_ids: string[];
  drafts: CampaignDraft[];
  skips: CampaignSkip[];
  events: CampaignEvent[];
}

export interface CampaignEvent {
  event_type: string;
  actor_email: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface CampaignList {
  items: CampaignSummary[];
}

export function listCampaigns(includeArchived = false): Promise<CampaignList> {
  return apiRequest<CampaignList>(
    `/campaigns${includeArchived ? "?include_archived=true" : ""}`,
  );
}

export function getCampaign(id: string): Promise<CampaignDetail> {
  return apiRequest<CampaignDetail>(`/campaigns/${encodeURIComponent(id)}`);
}

export function previewCampaign(input: CampaignInput): Promise<CampaignPreview> {
  return apiRequest<CampaignPreview>("/campaigns/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function createCampaign(input: CampaignInput): Promise<CampaignDetail> {
  return apiRequest<CampaignDetail>("/campaigns", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function updateCampaign(
  id: string,
  input: CampaignInput,
): Promise<CampaignDetail> {
  return apiRequest<CampaignDetail>(`/campaigns/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function generateCampaign(id: string): Promise<CampaignDetail> {
  return apiRequest<CampaignDetail>(
    `/campaigns/${encodeURIComponent(id)}/generate`,
    { method: "POST" },
  );
}

export function archiveCampaign(id: string): Promise<CampaignDetail> {
  return apiRequest<CampaignDetail>(
    `/campaigns/${encodeURIComponent(id)}/archive`,
    { method: "POST" },
  );
}

export function restoreCampaign(id: string): Promise<CampaignDetail> {
  return apiRequest<CampaignDetail>(
    `/campaigns/${encodeURIComponent(id)}/restore`,
    { method: "POST" },
  );
}
