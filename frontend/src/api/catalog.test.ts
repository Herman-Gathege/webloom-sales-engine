import { afterEach, describe, expect, it, vi } from "vitest";

import {
  containsRawContact,
  createOffer,
  createTemplate,
  formatPriceRange,
  variablesInBody,
} from "./catalog";

describe("catalog API", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("sends multi-currency offer values to the API", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "offer-1",
          name: "Starter Website",
          slug: "starter-website",
          description: null,
          price_min: "40000.00",
          price_max: "40000.00",
          currency: "USD",
          pitch_angle: null,
          is_active: true,
          created_at: "2026-11-02T00:00:00Z",
          updated_at: "2026-11-02T00:00:00Z",
        }),
        { status: 201, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await createOffer({
      name: "Starter Website",
      slug: "starter-website",
      description: null,
      price_min: "40000.00",
      price_max: "40000.00",
      currency: "USD",
      pitch_angle: null,
      is_active: true,
    });

    const body = JSON.parse(fetchMock.mock.calls[0][1].body as string);
    expect(body.currency).toBe("USD");
    expect(body.price_min).toBe("40000.00");
  });

  it("derives template variables and submits them", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "template-1",
          offer_id: "offer-1",
          channel: "sms",
          name: "Starter A",
          variant: "A",
          body: "Hi {{business_name}} {{opt_out}}",
          variables: ["business_name", "opt_out"],
          is_active: true,
          created_at: "2026-11-02T00:00:00Z",
          updated_at: "2026-11-02T00:00:00Z",
        }),
        { status: 201, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const body = "Hi {{business_name}} {{opt_out}}";

    await createTemplate({
      offer_id: "offer-1",
      channel: "sms",
      name: "Starter A",
      variant: "A",
      body,
      variables: variablesInBody(body),
      is_active: true,
    });

    const payload = JSON.parse(fetchMock.mock.calls[0][1].body as string);
    expect(payload.variables).toEqual(["business_name", "opt_out"]);
  });

  it("formats price ranges in the selected currency", () => {
    expect(formatPriceRange("40000.00", "40000.00", "KES")).toContain("40,000");
    expect(formatPriceRange(null, null, "USD")).toBe("Price guidance pending");
  });

  it("recognises raw phone and email values", () => {
    expect(containsRawContact("Call 0712 345678.")).toBe(true);
    expect(containsRawContact("Email owner@example.test.")).toBe(true);
    expect(containsRawContact("Hi {{business_name}} from {{area}}.")).toBe(false);
  });
});
