import { afterEach, describe, expect, it, vi } from "vitest";

import { sampleLeads } from "./fixtures";
import {
  ApiError,
  getLead,
  listLeads,
  recordSuppression,
  rejectedRowsCsv,
  reviewEligibility,
} from "./leads";

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

describe("rejectedRowsCsv", () => {
  it("writes a header and one line per refused row, quoting commas and quotes", () => {
    const csv = rejectedRowsCsv({
      filename: "list.csv",
      batch_id: "30000000-0000-4000-8000-000000000001",
      row_count: 2,
      accepted: 0,
      rejected: 2,
      duplicates: 1,
      requiring_review: 0,
      rejected_rows: [
        {
          row: 7,
          business_name: 'Mwangaza, "The" Hardware',
          code: "duplicate_phone",
          reason: "This phone number is already on row 3 of the file.",
        },
        {
          row: 19,
          business_name: "Riverside Dental",
          code: "missing_phone",
          reason: "No phone number, so this lead cannot be contacted.",
        },
      ],
      warnings: [],
    });

    expect(csv).toBe(
      "row,business_name,code,reason\n" +
        '7,"Mwangaza, ""The"" Hardware",duplicate_phone,This phone number is already on row 3 of the file.\n' +
        "19,Riverside Dental,missing_phone,\"No phone number, so this lead cannot be contacted.\"\n",
    );
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

describe("compliance mutations", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends one channel review to the API without using sample fallback", async () => {
    const updated = {
      ...sampleLeader(),
      provenance: null,
      eligibility: [],
      suppressions: [],
    };
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(updated), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await reviewEligibility(sampleLeads[0].id, "email", {
      state: "needs_review",
      lawful_basis: null,
      evidence_summary: null,
      evidence_source: null,
      intended_purpose: null,
      contact_context: null,
      reviewer: "Anne",
      rationale: "More evidence needed.",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      `/api/v1/leads/${sampleLeads[0].id}/eligibility/email`,
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({
          state: "needs_review",
          lawful_basis: null,
          evidence_summary: null,
          evidence_source: null,
          intended_purpose: null,
          contact_context: null,
          reviewer: "Anne",
          rationale: "More evidence needed.",
        }),
      }),
    );
  });

  it("sends a terminal suppression and surfaces API validation text", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "This lead has no contact available." }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      recordSuppression(sampleLeads[0].id, {
        scope: "all_marketing",
        reason: "opt_out",
        source: "Written request",
        recorded_by: "Anne",
        note: null,
      }),
    ).rejects.toThrow("This lead has no contact available.");

    expect(fetchMock).toHaveBeenCalledWith(
      `/api/v1/leads/${sampleLeads[0].id}/suppressions`,
      expect.objectContaining({ method: "POST" }),
    );
  });
});

describe("the Lead contract", () => {
  // If this fails, either the fixtures drifted or the agreed contract changed.
  // The contract lives in docs/delivery/sprint-1-lead-contract.md.
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
        "email",
        "whatsapp_capable",
        "website_status",
        "has_website",
        "source",
        "status",
        "created_at",
        "updated_at",
        "activity",
        "provenance",
        "eligibility",
        "suppressions",
      ].sort(),
    );

    expect(Object.keys(activity).sort()).toEqual(
      ["id", "lead_id", "type", "actor", "summary", "details", "created_at"].sort(),
    );
  });
});

function sampleLeader() {
  return sampleLeads[0];
}
