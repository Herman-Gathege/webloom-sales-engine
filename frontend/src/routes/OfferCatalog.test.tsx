import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OfferCatalog } from "./OfferCatalog";

const mocks = vi.hoisted(() => ({
  role: "admin",
  listOffers: vi.fn(),
  createOffer: vi.fn(),
  updateOffer: vi.fn(),
}));

vi.mock("@/auth/context", () => ({
  useAuth: () => ({ user: { role: mocks.role } }),
}));

vi.mock("@/api/catalog", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/api/catalog")>();
  return {
    ...original,
    listOffers: mocks.listOffers,
    createOffer: mocks.createOffer,
    updateOffer: mocks.updateOffer,
  };
});

const offer = {
  id: "offer-1",
  name: "Starter Website",
  slug: "starter-website",
  description: "A focused first website.",
  price_min: "40000.00",
  price_max: "40000.00",
  currency: "KES",
  pitch_angle: "A clear starting point.",
  is_active: true,
  created_at: "2026-11-02T00:00:00Z",
  updated_at: "2026-11-02T00:00:00Z",
};

describe("OfferCatalog", () => {
  beforeEach(() => {
    mocks.role = "admin";
    mocks.listOffers.mockReset();
    mocks.createOffer.mockReset();
    mocks.updateOffer.mockReset();
    mocks.listOffers.mockResolvedValue([offer]);
    mocks.createOffer.mockResolvedValue(offer);
    mocks.updateOffer.mockResolvedValue({ ...offer, is_active: false });
  });

  it("shows offers and admin create controls", async () => {
    render(
      <MemoryRouter>
        <OfferCatalog />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Starter Website")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "New offer" }));
    expect(screen.getByRole("dialog")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "New offer" })).toBeTruthy();
    expect(screen.getByText(/40,000/)).toBeTruthy();
  });

  it("hides mutation controls from sales users", async () => {
    mocks.role = "sales";
    render(
      <MemoryRouter>
        <OfferCatalog />
      </MemoryRouter>,
    );

    await screen.findByText("Starter Website");
    expect(screen.queryByRole("button", { name: "New offer" })).toBeNull();
  });

  it("submits a new offer and deactivates an existing offer", async () => {
    render(
      <MemoryRouter>
        <OfferCatalog />
      </MemoryRouter>,
    );

    await screen.findByText("Starter Website");
    fireEvent.click(screen.getByRole("button", { name: "New offer" }));
    fireEvent.change(screen.getByLabelText("Name"), {
      target: { value: "Review Offer" },
    });
    fireEvent.change(screen.getByLabelText("Slug"), {
      target: { value: "review-offer" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create offer" }));

    await waitFor(() =>
      expect(mocks.createOffer).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "Review Offer",
          slug: "review-offer",
          currency: "KES",
        }),
      ),
    );

    fireEvent.click(screen.getByRole("button", { name: "Deactivate" }));
    await waitFor(() =>
      expect(mocks.updateOffer).toHaveBeenCalledWith(offer.id, {
        is_active: false,
      }),
    );
  });
});
