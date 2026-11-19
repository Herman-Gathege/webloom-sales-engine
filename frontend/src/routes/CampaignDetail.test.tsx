import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CampaignDetail } from "./CampaignDetail";

const mocks = vi.hoisted(() => ({
  getCampaign: vi.fn(),
  generateCampaign: vi.fn(),
  archiveCampaign: vi.fn(),
  restoreCampaign: vi.fn(),
}));

vi.mock("@/auth/context", () => ({
  useAuth: () => ({ user: { id: "owner-1", role: "sales" } }),
}));
vi.mock("@/api/campaign", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/api/campaign")>();
  return {
    ...original,
    getCampaign: mocks.getCampaign,
    generateCampaign: mocks.generateCampaign,
    archiveCampaign: mocks.archiveCampaign,
    restoreCampaign: mocks.restoreCampaign,
  };
});

const summary = {
  id: "campaign-1",
  name: "Westlands campaign",
  goal: "Book five calls.",
  channel: "sms" as const,
  owner_id: "owner-1",
  owner_email: "owner@example.test",
  offer_id: "offer-1",
  offer_name: "Starter Website",
  template_id: "template-1",
  template_name: "Website starter A",
  selected_count: 1,
  draft_count: 0,
  skip_count: 0,
  status: "draft" as const,
  created_at: "2026-11-19T09:00:00Z",
  updated_at: "2026-11-19T09:00:00Z",
  last_activity_at: "2026-11-19T09:00:00Z",
  generated_at: null,
  archived_at: null,
  archived_by_email: null,
};

const draftCampaign = {
  ...summary,
  status: "generated" as const,
  draft_count: 1,
  generated_at: "2026-11-19T10:00:00Z",
  offer_snapshot: {},
  template_snapshot: {},
  input_fingerprint: "a".repeat(64),
  selection_context: { area: "Westlands" },
  selected_lead_ids: ["lead-1"],
  drafts: [
    {
      id: "draft-1",
      lead_id: "lead-1",
      business_name: "Synthetic Clinic",
      sector: "Clinics",
      area: "Westlands",
      channel: "sms" as const,
      state: "draft" as const,
      rendered_body: "Hello Synthetic Clinic. Reply STOP to opt out.",
      sms_encoding: "gsm-7",
      sms_characters: 48,
      sms_units: 48,
      sms_segments: 1,
      eligibility_snapshot: {
        decision_type: "automated_policy",
        policy_id: "yellow-pages-generic-business-sms-v1",
        policy_version: "1",
      },
      template_snapshot: {},
      offer_snapshot: {},
      generated_at: "2026-11-19T10:00:00Z",
      research_date: "2026-11-19",
      research_stale: false,
    },
  ],
  skips: [],
  events: [],
};

describe("CampaignDetail", () => {
  beforeEach(() => {
    mocks.getCampaign.mockReset().mockResolvedValue({
      ...summary,
      offer_snapshot: {},
      template_snapshot: {},
      input_fingerprint: "a".repeat(64),
      selection_context: { area: "Westlands" },
      selected_lead_ids: ["lead-1"],
      drafts: [],
      skips: [],
      events: [],
    });
    mocks.generateCampaign.mockReset().mockResolvedValue(draftCampaign);
    mocks.archiveCampaign.mockReset();
    mocks.restoreCampaign.mockReset();
  });

  it("warns that generation is final and never sends", async () => {
    render(
      <MemoryRouter initialEntries={["/campaigns/campaign-1"]}>
        <Routes>
          <Route path="/campaigns/:id" element={<CampaignDetail />} />
        </Routes>
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByRole("button", { name: "Generate drafts" }));
    expect(screen.getByText(/cannot be edited or regenerated/i)).toBeTruthy();
    expect(screen.getByText(/Not sent/i)).toBeTruthy();
    fireEvent.click(screen.getAllByRole("button", { name: "Generate drafts" }).at(-1)!);

    await waitFor(() => expect(mocks.generateCampaign).toHaveBeenCalledWith("campaign-1"));
    expect(await screen.findByText("Not sent")).toBeTruthy();
    expect(screen.getByText(/48 characters/)).toBeTruthy();
    expect(screen.getByText(/1 segment/)).toBeTruthy();
    expect(screen.getByText("area")).toBeTruthy();
  });

  it("warns when an SMS draft needs multiple paid segments", async () => {
    mocks.getCampaign.mockResolvedValue({
      ...draftCampaign,
      drafts: [
        {
          ...draftCampaign.drafts[0],
          sms_characters: 172,
          sms_units: 172,
          sms_segments: 2,
        },
      ],
    });
    render(
      <MemoryRouter initialEntries={["/campaigns/campaign-1"]}>
        <Routes>
          <Route path="/campaigns/:id" element={<CampaignDetail />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText(/needs 2 SMS segments/i)).toBeTruthy();
  });
});
