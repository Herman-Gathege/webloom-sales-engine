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

    // The last step of the Epic 1 demo: "See basic activity/history".
    expect(await screen.findByText("Activity")).toBeTruthy();
    for (const entry of lead.activity) {
      expect(screen.getByText(entry.summary)).toBeTruthy();
    }
  });
});
