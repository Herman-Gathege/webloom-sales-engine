import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ImportSummary } from "@/api/types";
import { LeadImport } from "./LeadImport";

const mocks = vi.hoisted(() => ({ importLeads: vi.fn() }));

vi.mock("@/api/leads", () => ({
  importLeads: mocks.importLeads,
  rejectedRowsCsv: () => "row,business_name,code,reason\n",
}));

const summary: ImportSummary = {
  filename: "webloom-lead-list.csv",
  row_count: 52,
  accepted: 50,
  rejected: 2,
  rejected_rows: [
    {
      row: 7,
      business_name: "Mwangaza Hardware",
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
  warnings: [
    {
      row: 12,
      field: "website_status",
      value: "does not say",
      code: "website_status_unclassified",
      message: "Website status kept as written; has_website left false.",
    },
  ],
};

function renderScreen() {
  return render(
    <MemoryRouter>
      <LeadImport />
    </MemoryRouter>,
  );
}

function chooseFile() {
  const input = screen.getByLabelText(/choose a csv/i);
  fireEvent.change(input, {
    target: { files: [new File(["Business\n"], "webloom-lead-list.csv", { type: "text/csv" })] },
  });
}

describe("LeadImport", () => {
  beforeEach(() => {
    mocks.importLeads.mockReset();
  });

  it("starts with nothing to import", () => {
    renderScreen();

    expect(screen.getByRole("button", { name: "Import" })).toHaveProperty("disabled", true);
    expect(screen.queryByText(/rows read/i)).toBeNull();
  });

  it("shows what happened to every row, with the reasons", async () => {
    mocks.importLeads.mockImplementation(
      async (_file: File, onProgress?: (percent: number) => void) => {
        onProgress?.(100);
        return summary;
      },
    );

    renderScreen();
    chooseFile();
    fireEvent.click(screen.getByRole("button", { name: "Import" }));

    // Wait for the summary; while the upload runs there is a different status.
    await screen.findByText("Refused rows");
    const counts = screen
      .getAllByRole("status")
      .map((element) => element.textContent ?? "")
      .join(" ");
    expect(counts).toContain("52 rows read");
    expect(counts).toContain("50 imported");
    expect(counts).toContain("2 refused");

    expect(screen.getByText("Mwangaza Hardware")).toBeTruthy();
    expect(screen.getByText("This phone number is already on row 3 of the file.")).toBeTruthy();
    expect(screen.getByText("Riverside Dental")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Download refused rows" })).toBeTruthy();
    expect(
      screen.getByText("Website status kept as written; has_website left false."),
    ).toBeTruthy();
  });

  it("shows the server's reason when the file is refused", async () => {
    mocks.importLeads.mockRejectedValue(
      new Error("The file is missing these columns: Phone."),
    );

    renderScreen();
    chooseFile();
    fireEvent.click(screen.getByRole("button", { name: "Import" }));

    expect(await screen.findByRole("alert")).toHaveProperty(
      "textContent",
      "The file is missing these columns: Phone.",
    );
  });
});
