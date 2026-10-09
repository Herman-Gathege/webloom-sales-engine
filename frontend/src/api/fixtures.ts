/**
 * Synthetic sample data for Epic 1.
 *
 * These are invented businesses with invented phone numbers. Real lead data
 * lives in the gitignored `data/` directory and must never be committed or
 * pasted into a component.
 *
 * The sector mix is modelled on the real list audit:
 * docs/research/2026-10-08-lead-list-audit.md
 */

import type { Activity, Lead, LeadDetail } from "./types";

const CREATED = "2026-09-23T09:00:00Z";

function lead(
  n: number,
  business_name: string,
  sector: string,
  area: string,
  website_status: string,
  whatsapp_capable = true,
): Lead {
  return {
    id: `00000000-0000-4000-8000-0000000000${String(n).padStart(2, "0")}`,
    business_name,
    sector,
    area,
    phone: `+2547000001${String(n).padStart(2, "0")}`,
    whatsapp_capable,
    website_status,
    has_website: false,
    source: "google_maps",
    status: "new",
    created_at: CREATED,
    updated_at: CREATED,
  };
}

export const sampleLeads: Lead[] = [
  lead(
    1,
    "Mwangaza Opticians",
    "Opticians and eyewear",
    "CBD, 3 branches",
    "3,713 reviews - no website listed",
  ),
  lead(
    2,
    "Green Valley Agrovet",
    "Agrovets and agri-input suppliers",
    "Kiambu Road",
    "212 reviews - no website listed",
  ),
  lead(
    3,
    "Riverside Dental Centre",
    "Clinics, dental and medical centres",
    "Westlands",
    "488 reviews - Facebook page only",
  ),
  lead(
    4,
    "Sokoni Hardware and Electricals",
    "Hardware, electrical and security suppliers",
    "Industrial Area",
    "76 reviews - no website listed",
  ),
  lead(
    5,
    "Swiftline Logistics",
    "Logistics, freight and removals",
    "Mombasa Road",
    "34 reviews - Instagram only",
  ),
  lead(
    6,
    "Baraka Chemist",
    "Pharmacies and chemists",
    "Ngong Road",
    "landline only - no website listed",
    false,
  ),
];

/** Two history entries per lead, so the detail screen has something to render. */
export const sampleActivity: Activity[] = sampleLeads.flatMap((entry, i) => [
  {
    id: `10000000-0000-4000-8000-0000000000${String(i * 2 + 1).padStart(2, "0")}`,
    lead_id: entry.id,
    type: "lead.created",
    actor: "system",
    summary: "Imported from the Google Maps list",
    created_at: CREATED,
  },
  {
    id: `10000000-0000-4000-8000-0000000000${String(i * 2 + 2).padStart(2, "0")}`,
    lead_id: entry.id,
    type: "lead.researched",
    actor: "system",
    summary: `Website research recorded: ${entry.website_status}`,
    created_at: "2026-09-23T09:05:00Z",
  },
]);

export const sampleLeadDetails: LeadDetail[] = sampleLeads.map((entry) => ({
  ...entry,
  activity: sampleActivity
    .filter((a) => a.lead_id === entry.id)
    .sort((a, b) => a.created_at.localeCompare(b.created_at)),
}));
