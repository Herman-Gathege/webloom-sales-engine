import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CampaignList } from "./CampaignList";

const mocks = vi.hoisted(() => ({ listCampaigns: vi.fn() }));

vi.mock("@/api/campaign", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/api/campaign")>();
  return { ...original, listCampaigns: mocks.listCampaigns };
});

const campaign = {
  id: "00000000-0000-4000-8000-000000000101",
  name: "Westlands campaign",
  goal: "Book five calls.",
  channel: "sms" as const,
  owner_id: "00000000-0000-4000-8000-000000000001",
  owner_email: "owner@example.test",
  offer_id: "offer-1",
  offer_name: "Starter Website",
  template_id: "template-1",
  template_name: "Website starter A",
  selected_count: 5,
  draft_count: 3,
  skip_count: 2,
  status: "generated" as const,
  created_at: "2026-11-19T09:00:00Z",
  updated_at: "2026-11-19T09:00:00Z",
  last_activity_at: "2026-11-19T09:00:00Z",
  generated_at: "2026-11-19T10:00:00Z",
  archived_at: null,
  archived_by_email: null,
};

describe("CampaignList", () => {
  beforeEach(() => {
    mocks.listCampaigns.mockReset();
    mocks.listCampaigns.mockResolvedValue({ items: [campaign] });
  });

  it("lists campaign outcomes and lets the user include archives", async () => {
    render(
      <MemoryRouter initialEntries={["/campaigns"]}>
        <CampaignList />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Westlands campaign")).toBeTruthy();
    expect(screen.getByText(/3 drafts/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "New campaign" }).getAttribute("href")).toBe(
      "/campaigns/new",
    );

    fireEvent.click(screen.getByLabelText("Show archived campaigns"));

    await waitFor(() => expect(mocks.listCampaigns).toHaveBeenLastCalledWith(true));
  });
});
