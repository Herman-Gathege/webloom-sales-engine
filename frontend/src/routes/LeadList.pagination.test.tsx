import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Lead } from "@/api/types";
import { LeadList } from "./LeadList";

const mocks = vi.hoisted(() => ({ listLeads: vi.fn() }));

vi.mock("@/api/leads", () => ({ listLeads: mocks.listLeads }));

function makeLeads(count: number): Lead[] {
  return Array.from({ length: count }, (_, index) => ({
    id: `00000000-0000-4000-8000-${String(index).padStart(12, "0")}`,
    business_name: `Business ${index + 1}`,
    sector: "Opticians and eyewear",
    area: "CBD",
    phone: `+2547000${String(index).padStart(5, "0")}`,
    whatsapp_capable: true,
    website_status: "no website listed",
    has_website: false,
    source: "google_maps",
    status: "new" as const,
    created_at: "2026-10-19T09:00:00Z",
    updated_at: "2026-10-19T09:00:00Z",
  }));
}

describe("LeadList pagination", () => {
  beforeEach(() => {
    mocks.listLeads.mockReset();
    mocks.listLeads.mockResolvedValue({
      source: "api",
      data: { items: makeLeads(60), total: 60, limit: 200, offset: 0 },
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
  });
});
