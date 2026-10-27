import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { sampleLeadDetails } from "@/api/fixtures";
import { CompliancePanel } from "./CompliancePanel";

const mocks = vi.hoisted(() => ({
  reviewEligibility: vi.fn(),
  recordSuppression: vi.fn(),
}));

vi.mock("@/api/leads", () => ({
  reviewEligibility: mocks.reviewEligibility,
  recordSuppression: mocks.recordSuppression,
}));

const lead = sampleLeadDetails[0];

describe("CompliancePanel", () => {
  beforeEach(() => {
    mocks.reviewEligibility.mockReset();
    mocks.recordSuppression.mockReset();
  });

  it("submits one channel review without changing the others", async () => {
    const user = userEvent.setup();
    mocks.reviewEligibility.mockResolvedValue(lead);
    render(<CompliancePanel lead={lead} sampleMode={false} onUpdated={vi.fn()} />);

    await user.click(screen.getByText("Review email"));
    await user.click(screen.getByRole("button", { name: "Save email review" }));

    expect(mocks.reviewEligibility).toHaveBeenCalledWith(
      lead.id,
      "email",
      expect.objectContaining({
        state: "eligible",
        reviewer: "Anne",
        lawful_basis: "legitimate_interests",
      }),
    );
  });

  it("requires explicit confirmation before an all-marketing restriction", async () => {
    const user = userEvent.setup();
    mocks.recordSuppression.mockResolvedValue(lead);
    render(<CompliancePanel lead={lead} sampleMode={false} onUpdated={vi.fn()} />);

    await user.type(screen.getByLabelText("Suppression source"), "Written request");
    await user.type(screen.getByLabelText("Suppression recorder"), "Anne");
    const save = screen.getByRole("button", { name: "Record restriction" });
    expect(save).toHaveProperty("disabled", true);

    await user.click(screen.getByLabelText("Confirm all-marketing suppression"));
    expect(save).toHaveProperty("disabled", false);
    await user.click(save);

    expect(mocks.recordSuppression).toHaveBeenCalledWith(
      lead.id,
      expect.objectContaining({
        scope: "all_marketing",
        reason: "opt_out",
        source: "Written request",
        recorded_by: "Anne",
      }),
    );
  });

  it("disables every mutation in sample mode", async () => {
    render(<CompliancePanel lead={lead} sampleMode onUpdated={vi.fn()} />);

    expect(screen.getByText(/controls are disabled while the app is showing sample data/i))
      .toBeTruthy();
    expect(screen.getByRole("button", { name: "Record restriction" })).toHaveProperty(
      "disabled",
      true,
    );
  });

  it("shows the automatic outcome separately from human channel evidence", () => {
    render(<CompliancePanel lead={lead} sampleMode onUpdated={vi.fn()} />);

    expect(screen.getByText("Automatic eligibility result")).toBeTruthy();
    expect(screen.getByText("Automatic channel gate")).toBeTruthy();
    expect(screen.getByText(lead.compliance.explanation)).toBeTruthy();
    expect(screen.getByText("Current human decision")).toBeTruthy();
  });
});
