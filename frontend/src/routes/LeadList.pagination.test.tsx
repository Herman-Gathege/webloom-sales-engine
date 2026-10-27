import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Lead } from "@/api/types";
import { LeadList } from "./LeadList";

const mocks = vi.hoisted(() => ({ listLeads: vi.fn(), getLeadFilterOptions: vi.fn() }));

vi.mock("@/api/leads", () => ({
  listLeads: mocks.listLeads,
  getLeadFilterOptions: mocks.getLeadFilterOptions,
}));

function makeLeads(count: number): Lead[] {
  return Array.from({ length: count }, (_, index) => ({
    id: `00000000-0000-4000-8000-${String(index).padStart(12, "0")}`,
    business_name: `Business ${index + 1}`,
    sector: "Opticians and eyewear",
    area: "CBD",
    phone: `+2547000${String(index).padStart(5, "0")}`,
    email: `business${index + 1}@example.test`,
    whatsapp_capable: true,
    website_status: "no website listed",
    has_website: false,
    source: "google_maps",
    status: "new" as const,
    created_at: "2026-10-19T09:00:00Z",
    updated_at: "2026-10-19T09:00:00Z",
    compliance: {
      status: "needs_review" as const,
      data_quality_status: "complete" as const,
      reason_codes: ["human_review_required:email"],
      explanation: "Needs review: a human decision is required.",
      eligible_channels: [],
      suppressed_channels: [],
      channel_results: [],
      outreach_ready: false,
      evaluated_at: "2026-10-19T09:00:00Z",
      rule_version: "2026-10-27.1",
    },
  }));
}

describe("LeadList pagination", () => {
  beforeEach(() => {
    mocks.listLeads.mockReset();
    mocks.getLeadFilterOptions.mockReset();
    mocks.getLeadFilterOptions.mockResolvedValue({
      source: "api",
      data: {
        sectors: ["Opticians and eyewear"],
        areas: ["CBD"],
        sources: ["google_maps"],
        statuses: ["new"],
        compliance_statuses: ["eligible", "needs_review", "blocked", "invalid"],
        data_quality_statuses: ["complete", "incomplete", "invalid"],
        import_batches: [],
      },
    });
    mocks.listLeads.mockImplementation(async (params = {}) => {
      const limit = params.limit ?? 50;
      const offset = params.offset ?? 0;
      return {
        source: "api",
        data: { items: makeLeads(60).slice(offset, offset + limit), total: 60, limit, offset },
      };
    });
  });

  it("shows the first page and walks to the next", async () => {
    render(
      <MemoryRouter initialEntries={["/leads"]}>
        <LeadList />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/showing 1.25 of 60/i)).toBeTruthy();
    expect(screen.getByText("Business 1")).toBeTruthy();
    expect(screen.queryByText("Business 26")).toBeNull();
    expect(screen.getByRole("button", { name: "Previous" })).toHaveProperty("disabled", true);

    fireEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(await screen.findByText(/showing 26.50 of 60/i)).toBeTruthy();
    expect(screen.getByText("Business 26")).toBeTruthy();
    expect(screen.queryByText("Business 1")).toBeNull();
    expect(screen.getByText(/page 2 of 3/i)).toBeTruthy();
  }, 10_000);
});
