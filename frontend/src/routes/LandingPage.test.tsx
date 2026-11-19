import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { LandingPage } from "./LandingPage";

describe("LandingPage", () => {
  it("presents the product promise and a labelled demonstration preview", () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", {
        name: "Find the right prospects. Build better conversations.",
      }),
    ).toBeTruthy();
    expect(screen.getByText("Demonstration data")).toBeTruthy();
    expect(screen.getAllByRole("link", { name: "Get started" })).toHaveLength(3);
    expect(screen.getByRole("heading", { name: "Prospect organisation" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Outreach management" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Lead prioritisation" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Team visibility" })).toBeTruthy();
  });

  it("opens the mobile navigation", () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Open navigation" }));

    expect(screen.getByRole("navigation", { name: "Mobile product navigation" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Close navigation" })).toBeTruthy();
  });
});
