import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Lead } from "@/api/types";
import { LeadList } from "./LeadList";

const mocks = vi.hoisted(() => ({
  createLead: vi.fn(),
  getLeadFilterOptions: vi.fn(),
  listLeads: vi.fn(),
}));

vi.mock("@/api/leads", () => ({
  createLead: mocks.createLead,
  getLeadFilterOptions: mocks.getLeadFilterOptions,
  listLeads: mocks.listLeads,
}));

const createdLead: Lead = {
  id: "00000000-0000-4000-8000-000000000099",
  business_name: "Synthetic Manual Optician",
  sector: "Opticians and eyewear",
  area: "Westlands",
  phone: "+254712345678",
  email: null,
  whatsapp_capable: true,
  website_status: "No website listed",
  has_website: false,
  website_presence: "no_website",
  source: "manual_entry",
  status: "new",
  created_at: "2026-11-09T09:00:00Z",
  updated_at: "2026-11-09T09:00:00Z",
  compliance: {
    status: "needs_review",
    data_quality_status: "complete",
    reason_codes: ["no_approved_policy:sms"],
    explanation: "Needs review: no approved policy matches this channel.",
    eligible_channels: [],
    suppressed_channels: [],
    channel_results: [],
    outreach_ready: false,
    evaluated_at: "2026-11-09T09:00:00Z",
    rule_version: "2026-11-09.1",
  },
};

function renderLeadList() {
  return render(
    <MemoryRouter initialEntries={["/leads"]}>
      <LeadList />
    </MemoryRouter>,
  );
}

describe("LeadList manual creation", () => {
  beforeEach(() => {
    mocks.createLead.mockReset();
    mocks.listLeads.mockReset();
    mocks.getLeadFilterOptions.mockReset();
    mocks.getLeadFilterOptions.mockResolvedValue({
      source: "api",
      data: {
        sectors: [],
        areas: [],
        sources: [],
        statuses: [],
        compliance_statuses: ["eligible", "needs_review", "blocked", "invalid"],
        data_quality_statuses: ["complete", "incomplete", "invalid"],
        import_batches: [],
      },
    });
    mocks.listLeads.mockResolvedValue({
      source: "api",
      data: { items: [], total: 0, limit: 25, offset: 0 },
    });
  });

  it("creates a lead and brings it straight into the Lead Desk", async () => {
    mocks.createLead.mockImplementation(async () => {
      mocks.listLeads.mockResolvedValue({
        source: "api",
        data: { items: [createdLead], total: 1, limit: 25, offset: 0 },
      });
      return createdLead;
    });

    renderLeadList();
    fireEvent.click(await screen.findByRole("button", { name: "Add lead" }));

    expect(screen.getByRole("dialog", { name: "Add one lead" })).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Business name"), {
      target: { value: "Synthetic Manual Optician" },
    });
    fireEvent.change(screen.getByLabelText(/^Phone/), {
      target: { value: "0712 345 678" },
    });
    fireEvent.change(screen.getByLabelText(/^Website status/), {
      target: { value: "No website listed" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save lead" }));

    await waitFor(() => expect(mocks.createLead).toHaveBeenCalledTimes(1));
    expect(mocks.createLead).toHaveBeenCalledWith(
      expect.objectContaining({
        business_name: "Synthetic Manual Optician",
        phone: "0712 345 678",
        source: "Manual entry",
      }),
    );
    expect(await screen.findByText("Synthetic Manual Optician")).toBeTruthy();
    await waitFor(() => {
      expect(
        screen
          .getAllByRole("status")
          .map((element) => element.textContent ?? "")
          .join(" "),
      ).toContain("Synthetic Manual Optician was added.");
    });
    await waitFor(() =>
      expect(mocks.listLeads).toHaveBeenCalledWith(
        expect.objectContaining({ q: "Synthetic Manual Optician" }),
      ),
    );
  });

  it("does not submit twice while the first save is still running", async () => {
    let release: (lead: Lead) => void = () => undefined;
    mocks.createLead.mockImplementation(
      () =>
        new Promise<Lead>((resolve) => {
          release = resolve;
        }),
    );

    renderLeadList();
    fireEvent.click(await screen.findByRole("button", { name: "Add lead" }));
    fireEvent.change(screen.getByLabelText("Business name"), {
      target: { value: "Synthetic Manual Optician" },
    });
    fireEvent.change(screen.getByLabelText(/^Phone/), {
      target: { value: "0712 345 678" },
    });
    const save = screen.getByRole("button", { name: "Save lead" });
    fireEvent.click(save);
    fireEvent.click(save);

    expect(mocks.createLead).toHaveBeenCalledTimes(1);
    expect(save).toHaveProperty("disabled", true);
    await act(async () => {
      release(createdLead);
    });
  });
});
