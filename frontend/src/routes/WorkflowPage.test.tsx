import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { WorkflowPage } from "./WorkflowPage";

describe("WorkflowPage", () => {
  it("renders all six workflow stages with user, Wadi and why-it-matters detail", () => {
    render(
      <MemoryRouter>
        <WorkflowPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "How Wadi works" })).toBeTruthy();

    expect(screen.getByText("Import prospect information")).toBeTruthy();
    expect(screen.getByText("Organise leads")).toBeTruthy();
    expect(screen.getByText("Understand lead sources and information")).toBeTruthy();
    expect(screen.getByText("Apply outreach eligibility and compliance checks")).toBeTruthy();
    expect(screen.getByText("Select offers and templates")).toBeTruthy();
    expect(screen.getByText("Prepare campaign drafts")).toBeTruthy();

    // Each stage has a "You:", "Wadi:", "Why it matters:" label — six of each.
    expect(screen.getAllByText("You:")).toHaveLength(6);
    expect(screen.getAllByText("Wadi:")).toHaveLength(6);
    expect(screen.getAllByText("Why it matters:")).toHaveLength(6);
  });

  it("explains what the user does, what Wadi does and why it matters per stage", () => {
    render(
      <MemoryRouter>
        <WorkflowPage />
      </MemoryRouter>,
    );

    expect(screen.getByText(/Upload a CSV of researched businesses/)).toBeTruthy();
    expect(screen.getByText(/Keeps each lead's source, contact details/)).toBeTruthy();
    expect(screen.getByText(/Prospect information stops living across notes/)).toBeTruthy();

    expect(screen.getByText(/Checks every lead against outreach policy/)).toBeTruthy();
    expect(screen.getByText(/Public contact information is not blanket permission/)).toBeTruthy();

    expect(screen.getByText(/Nothing is sent automatically/)).toBeTruthy();
    expect(screen.getByText(/a person reviews and approves/)).toBeTruthy();
  });

  it("distinguishes existing functionality from future possibilities", () => {
    render(
      <MemoryRouter>
        <WorkflowPage />
      </MemoryRouter>,
    );

    expect(screen.getByText(/available in this release/)).toBeTruthy();
    expect(screen.getByText(/later sprints/)).toBeTruthy();
  });

  it("has working navigation links", () => {
    render(
      <MemoryRouter>
        <WorkflowPage />
      </MemoryRouter>,
    );

    // "Get started" appears in MarketingNav header and in the page footer CTA.
    expect(screen.getAllByRole("link", { name: "Get started" })).toHaveLength(2);
    expect(screen.getByRole("link", { name: "Back to overview" })).toBeTruthy();
  });

  it("opens the mobile navigation", () => {
    render(
      <MemoryRouter>
        <WorkflowPage />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Open navigation" }));

    expect(screen.getByRole("navigation", { name: "Mobile product navigation" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Close navigation" })).toBeTruthy();
  });
});
