import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { sampleLeads } from "@/api/fixtures";
import { LeadList } from "./LeadList";

describe("LeadList", () => {
  it("renders a row for every lead", async () => {
    render(
      <MemoryRouter>
        <LeadList />
      </MemoryRouter>,
    );

    // The first fixture proves the list rendered data, not a skeleton.
    expect(await screen.findByText(sampleLeads[0].business_name)).toBeTruthy();
    for (const lead of sampleLeads.slice(1)) {
      expect(screen.getByText(lead.business_name)).toBeTruthy();
    }
  });

  it("tells the user when it is showing sample data", async () => {
    render(
      <MemoryRouter>
        <LeadList />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/sample data/i)).toBeTruthy();
  });
});
