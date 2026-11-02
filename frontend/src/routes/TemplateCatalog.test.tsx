import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TemplateCatalog } from "./TemplateCatalog";

const mocks = vi.hoisted(() => ({
  role: "admin",
  listOffers: vi.fn(),
  listTemplates: vi.fn(),
}));

vi.mock("@/auth/context", () => ({
  useAuth: () => ({ user: { role: mocks.role } }),
}));

vi.mock("@/api/catalog", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/api/catalog")>();
  return {
    ...original,
    listOffers: mocks.listOffers,
    listTemplates: mocks.listTemplates,
  };
});

const offer = {
  id: "offer-1",
  name: "Starter Website",
  slug: "starter-website",
  description: null,
  price_min: "40000.00",
  price_max: "40000.00",
  currency: "KES",
  pitch_angle: null,
  is_active: true,
  created_at: "2026-11-02T00:00:00Z",
  updated_at: "2026-11-02T00:00:00Z",
};

const template = {
  id: "template-1",
  offer_id: "offer-1",
  channel: "sms",
  name: "Website starter A",
  variant: "A",
  body: "Hi {{business_name}} {{opt_out}}",
  variables: ["business_name", "opt_out"],
  is_active: true,
  created_at: "2026-11-02T00:00:00Z",
  updated_at: "2026-11-02T00:00:00Z",
};

describe("TemplateCatalog", () => {
  beforeEach(() => {
    mocks.role = "admin";
    mocks.listOffers.mockReset();
    mocks.listTemplates.mockReset();
    mocks.listOffers.mockResolvedValue([offer]);
    mocks.listTemplates.mockResolvedValue([template]);
  });

  it("shows templates and admin create controls", async () => {
    render(<TemplateCatalog />);

    expect(await screen.findByText("Website starter A")).toBeTruthy();
    expect(screen.getByText("business_name")).toBeTruthy();
    expect(screen.getByRole("button", { name: "New template" })).toBeTruthy();
  });

  it("hides mutation controls from sales users", async () => {
    mocks.role = "sales";
    render(<TemplateCatalog />);

    await screen.findByText("Website starter A");
    expect(screen.queryByRole("button", { name: "New template" })).toBeNull();
  });
});
