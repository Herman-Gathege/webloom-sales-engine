import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { sampleLeadDetails } from "@/api/fixtures";
import { LeadDetail } from "./LeadDetail";

const lead = sampleLeadDetails[0];

function renderDetail(id: string) {
  return render(
    <MemoryRouter initialEntries={[`/leads/${id}`]}>
      <Routes>
        <Route path="/leads/:id" element={<LeadDetail />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("LeadDetail", () => {
  it("renders the lead's fields", async () => {
    renderDetail(lead.id);

    expect(await screen.findByRole("heading", { name: lead.business_name })).toBeTruthy();
    expect(screen.getByText(lead.phone!)).toBeTruthy();
    expect(screen.getByText(lead.website_status!)).toBeTruthy();
  });

  it("renders the lead's activity history", async () => {
    renderDetail(lead.id);

    // The last step of the Sprint 1 demo: "See basic activity/history".
    expect(await screen.findByText("Activity")).toBeTruthy();
    for (const entry of lead.activity) {
      expect(screen.getByText(entry.summary)).toBeTruthy();
    }
  });

  it("shows provenance, independent channel state, and terminal suppression", async () => {
    renderDetail(lead.id);

    expect(await screen.findByText("Compliance review")).toBeTruthy();
    expect(screen.getByText("Synthetic research fixture")).toBeTruthy();
    expect(screen.getByText("30000000-0000-4000-8000-000000000001")).toBeTruthy();
    expect(screen.getAllByLabelText("Activity details").length).toBeGreaterThan(0);
    expect(screen.getAllByText("eligible").length).toBeGreaterThan(0);
    expect(screen.getAllByText("suppressed").length).toBeGreaterThan(0);
    expect(screen.getByText(/suppresses every available marketing channel/i)).toBeTruthy();
    expect(screen.getByText(/Review controls are disabled/i)).toBeTruthy();
  });
});
