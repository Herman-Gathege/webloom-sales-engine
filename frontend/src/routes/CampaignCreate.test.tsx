import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CampaignCreate } from "./CampaignCreate";

const mocks = vi.hoisted(() => ({
  listOffers: vi.fn(),
  listTemplates: vi.fn(),
  listLeads: vi.fn(),
  getLeadFilterOptions: vi.fn(),
  previewCampaign: vi.fn(),
  createCampaign: vi.fn(),
}));

vi.mock("@/api/catalog", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/api/catalog")>();
  return {
    ...original,
    listOffers: mocks.listOffers,
    listTemplates: mocks.listTemplates,
  };
});
vi.mock("@/api/leads", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/api/leads")>();
  return {
    ...original,
    listLeads: mocks.listLeads,
    getLeadFilterOptions: mocks.getLeadFilterOptions,
  };
});
vi.mock("@/api/campaign", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/api/campaign")>();
  return {
    ...original,
    previewCampaign: mocks.previewCampaign,
    createCampaign: mocks.createCampaign,
    getCampaign: vi.fn(),
    updateCampaign: vi.fn(),
  };
});

const offer = {
  id: "offer-1",
  name: "Starter Website",
  slug: "starter-website",
  description: null,
  price_min: "40000.00",
  price_max: null,
  currency: "KES",
  pitch_angle: null,
  is_active: true,
  created_at: "2026-11-19T09:00:00Z",
  updated_at: "2026-11-19T09:00:00Z",
};
const template = {
  id: "template-1",
  offer_id: offer.id,
  channel: "sms" as const,
  name: "Website starter A",
  variant: "A",
  body: "Hi {{business_name}} {{opt_out}}",
  variables: ["business_name", "opt_out"],
  is_active: true,
  created_at: "2026-11-19T09:00:00Z",
  updated_at: "2026-11-19T09:00:00Z",
};
const lead = {
  id: "00000000-0000-4000-8000-000000000201",
  business_name: "Synthetic Campaign Clinic",
  sector: "Clinics",
  area: "Westlands",
  phone: "+254700990401",
  email: null,
  whatsapp_capable: true,
  website_status: "no website listed",
  has_website: false,
  website_presence: "no_website" as const,
  source: "yellow_pages_kenya_listing",
  status: "new" as const,
  created_at: "2026-11-19T09:00:00Z",
  updated_at: "2026-11-19T09:00:00Z",
  compliance: {
    status: "eligible" as const,
    data_quality_status: "complete" as const,
    reason_codes: ["automated_policy_eligible:sms"],
    explanation: "SMS eligible.",
    eligible_channels: ["sms" as const],
    suppressed_channels: [],
    channel_results: [],
    outreach_ready: true,
    evaluated_at: "2026-11-19T09:00:00Z",
    rule_version: "2026-11-09.1",
  },
};

describe("CampaignCreate", () => {
  beforeEach(() => {
    mocks.listOffers.mockReset().mockResolvedValue([offer]);
    mocks.listTemplates.mockReset().mockResolvedValue([template]);
    mocks.getLeadFilterOptions.mockReset().mockResolvedValue({
      source: "api",
      data: {
        sectors: ["Clinics"],
        areas: ["Westlands"],
        sources: [lead.source],
        statuses: ["new"],
        compliance_statuses: ["eligible", "needs_review", "blocked", "invalid"],
        data_quality_statuses: ["complete", "incomplete", "invalid"],
        import_batches: [],
      },
    });
    mocks.listLeads.mockReset().mockResolvedValue({
      source: "api",
      data: { items: [lead], total: 1, limit: 25, offset: 0 },
    });
    mocks.previewCampaign.mockReset().mockResolvedValue({
      eligible_count: 1,
      skipped_count: 0,
      eligible: [
        {
          lead_id: lead.id,
          business_name: lead.business_name,
          sector: lead.sector,
          area: lead.area,
          source: lead.source,
          website_presence: "no_website",
          decision_type: "automated_policy",
          explanation: "SMS eligible.",
          policy_id: "yellow-pages-generic-business-sms-v1",
          policy_version: "1",
          technical_available: true,
          research_date: "2026-11-19",
          research_stale: false,
        },
      ],
      skipped: [],
      reason_counts: {},
    });
    mocks.createCampaign.mockReset().mockResolvedValue({
      id: "00000000-0000-4000-8000-000000000301",
    });
  });

  it("selects, previews and creates a campaign", async () => {
    render(
      <MemoryRouter initialEntries={["/campaigns/new"]}>
        <CampaignCreate />
      </MemoryRouter>,
    );

    await screen.findByText("Synthetic Campaign Clinic");
    fireEvent.change(screen.getByLabelText("Campaign sector filter"), {
      target: { value: "Clinics" },
    });
    fireEvent.change(screen.getByLabelText("Campaign name"), {
      target: { value: "Clinic campaign" },
    });
    fireEvent.change(screen.getByLabelText(/^Goal/), {
      target: { value: "Book five calls." },
    });
    fireEvent.click(screen.getByRole("checkbox", { name: /Synthetic Campaign Clinic/ }));
    fireEvent.click(screen.getByRole("button", { name: "Preview campaign" }));

    expect(await screen.findByText("1 eligible · 0 skipped")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Create campaign" }));
    await waitFor(() =>
      expect(mocks.createCampaign).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "Clinic campaign",
          goal: "Book five calls.",
          channel: "sms",
          lead_ids: [lead.id],
          selection_context: { sector: "Clinics" },
        }),
      ),
    );
  });
});
