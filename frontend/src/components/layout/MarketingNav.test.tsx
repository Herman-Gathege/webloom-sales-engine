import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { MarketingNav } from "./MarketingNav";

describe("MarketingNav", () => {
  it("renders the How it works, Sign in and Get started paths", () => {
    render(
      <MemoryRouter>
        <MarketingNav />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "How it works" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Sign in" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Get started" })).toBeTruthy();
  });

  it("no longer exposes a Product link in the desktop navigation", () => {
    render(
      <MemoryRouter>
        <MarketingNav />
      </MemoryRouter>,
    );

    expect(screen.queryByRole("link", { name: "Product" })).toBeNull();
  });

  it("opens the mobile navigation without a Product item", () => {
    render(
      <MemoryRouter>
        <MarketingNav />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Open navigation" }));

    expect(screen.getByRole("navigation", { name: "Mobile product navigation" })).toBeTruthy();
    expect(screen.queryAllByRole("link", { name: "Product" })).toHaveLength(0);
    expect(screen.getAllByRole("link", { name: "How it works" })).toHaveLength(2);
    expect(screen.getByRole("button", { name: "Close navigation" })).toBeTruthy();
  });
});
