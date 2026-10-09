import { describe, expect, it } from "vitest";

import { sampleLeads } from "./fixtures";
import { ApiError, getLead, listLeads } from "./leads";

// The vitest config sets VITE_USE_MOCK=1, so these exercise the sample-data
// path deterministically — no network, no flakiness. The live-API path is
// covered by the manual demo and by Sharon's backend tests.

describe("listLeads", () => {
  it("returns the leads with pagination metadata", async () => {
    const loaded = await listLeads();

    expect(loaded.source).toBe("sample");
    expect(loaded.data.items).toHaveLength(sampleLeads.length);
    expect(loaded.data.total).toBe(sampleLeads.length);
    expect(loaded.data.offset).toBe(0);
  });

  it("honours limit and offset", async () => {
    const loaded = await listLeads({ limit: 2, offset: 1 });

    expect(loaded.data.items).toHaveLength(2);
    expect(loaded.data.items[0].id).toBe(sampleLeads[1].id);
  });
});

describe("getLead", () => {
  it("returns one lead together with its activity", async () => {
    const loaded = await getLead(sampleLeads[0].id);

    expect(loaded.data.business_name).toBe(sampleLeads[0].business_name);
    expect(loaded.data.activity.length).toBeGreaterThan(0);
    expect(loaded.data.activity.every((entry) => entry.lead_id === loaded.data.id)).toBe(true);
  });

  it("rejects with a 404 for an unknown id", async () => {
    await expect(getLead("does-not-exist")).rejects.toBeInstanceOf(ApiError);
  });
});

describe("the Lead contract", () => {
  // If this fails, either the fixtures drifted or the agreed contract changed.
  // The contract lives in docs/delivery/epic-1-lead-contract.md.
  it("exposes exactly the agreed Lead and Activity fields", async () => {
    const loaded = await getLead(sampleLeads[0].id);
    const activity = loaded.data.activity[0];

    expect(Object.keys(loaded.data).sort()).toEqual(
      [
        "id",
        "business_name",
        "sector",
        "area",
        "phone",
        "whatsapp_capable",
        "website_status",
        "has_website",
        "source",
        "status",
        "created_at",
        "updated_at",
        "activity",
      ].sort(),
    );

    expect(Object.keys(activity).sort()).toEqual(
      ["id", "lead_id", "type", "actor", "summary", "created_at"].sort(),
    );
  });
});
