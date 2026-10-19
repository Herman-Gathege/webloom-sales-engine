import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { sampleLeads } from "@/api/fixtures";
import { LeadList } from "./LeadList";

/** The filters live in the URL, so rendering at a URL is the way to test them. */
function renderAt(url: string) {
  return render(
    <MemoryRouter initialEntries={[url]}>
      <LeadList />
    </MemoryRouter>,
  );
}

describe("LeadList", () => {
  it("renders a row for every lead", async () => {
    renderAt("/leads");

    // The first fixture proves the list rendered data, not a skeleton.
    expect(await screen.findByText(sampleLeads[0].business_name)).toBeTruthy();
    for (const lead of sampleLeads.slice(1)) {
      expect(screen.getByText(lead.business_name)).toBeTruthy();
    }
  });

  it("tells the user when it is showing sample data", async () => {
    renderAt("/leads");

    expect(await screen.findByText(/sample data/i)).toBeTruthy();
  });

  it("narrows the list by sector from the URL", async () => {
    const optician = sampleLeads.find((lead) => lead.sector === "Opticians and eyewear")!;
    const other = sampleLeads.find((lead) => lead.sector !== optician.sector)!;

    renderAt(`/leads?sector=${encodeURIComponent(optician.sector!)}`);

    expect(await screen.findByText(optician.business_name)).toBeTruthy();
    expect(screen.queryByText(other.business_name)).toBeNull();
    expect(screen.getByText(/showing 1 of/i)).toBeTruthy();
  });

  it("searches business name, phone and area", async () => {
    const match = sampleLeads.find((lead) => lead.area === "Westlands")!;
    const other = sampleLeads.find((lead) => lead.area !== "Westlands")!;

    renderAt("/leads?q=westlands");

    expect(await screen.findByText(match.business_name)).toBeTruthy();
    expect(screen.queryByText(other.business_name)).toBeNull();
  });

  it("finds a business by phone number", async () => {
    const match = sampleLeads[2];

    renderAt(`/leads?q=${encodeURIComponent(match.phone!)}`);

    expect(await screen.findByText(match.business_name)).toBeTruthy();
    expect(screen.queryByText(sampleLeads[0].business_name)).toBeNull();
  });

  it("says so when nothing matches", async () => {
    renderAt("/leads?q=zzzz-no-such-lead");

    expect(await screen.findByText(/no leads match these filters/i)).toBeTruthy();
  });

  it("filters by website status from the URL", async () => {
    // Every fixture is currently a no-website lead, so this proves the filter
    // is applied rather than simply ignored.
    renderAt("/leads?website=yes");

    expect(await screen.findByText(/no leads match these filters/i)).toBeTruthy();
  });

  it("filters by lead status from the URL", async () => {
    // Nothing has moved off "new" yet, so a contacted filter must be empty.
    renderAt("/leads?status=contacted");

    expect(await screen.findByText(/no leads match these filters/i)).toBeTruthy();
  });

  it("filters as the seller types", async () => {
    const match = sampleLeads.find((lead) => lead.business_name === "Baraka Chemist")!;
    const other = sampleLeads[0];

    renderAt("/leads");
    await screen.findByText(other.business_name);

    fireEvent.change(screen.getByLabelText("Search leads"), {
      target: { value: "baraka" },
    });

    expect(await screen.findByText(match.business_name)).toBeTruthy();
    expect(screen.queryByText(other.business_name)).toBeNull();
  });

  it("clears every filter", async () => {
    const optician = sampleLeads.find((lead) => lead.sector === "Opticians and eyewear")!;
    const other = sampleLeads.find((lead) => lead.sector !== optician.sector)!;

    renderAt(`/leads?sector=${encodeURIComponent(optician.sector!)}`);
    await screen.findByText(optician.business_name);

    fireEvent.click(screen.getByRole("button", { name: /^clear$/i }));

    expect(await screen.findByText(other.business_name)).toBeTruthy();
  });
});
