import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { ImportSummary } from "@/api/types";
import { LeadImport } from "./LeadImport";

const mocks = vi.hoisted(() => ({
  downloadImportTemplate: vi.fn(),
  importLeads: vi.fn(),
}));

vi.mock("@/api/leads", () => ({
  downloadImportTemplate: mocks.downloadImportTemplate,
  importLeads: mocks.importLeads,
  rejectedRowsCsv: () => "row,business_name,code,reason\n",
}));

const summary: ImportSummary = {
  filename: "webloom-lead-list.csv",
  batch_id: "30000000-0000-4000-8000-000000000001",
  row_count: 52,
  accepted: 50,
  created: 50,
  rejected: 2,
  matched: 1,
  duplicates: 1,
  eligible: 32,
  needs_review: 50,
  blocked: 0,
  invalid: 2,
  provenance_incomplete: 4,
  requiring_review: 18,
  automated_eligible: 32,
  suppressed_contacts: 1,
  incomplete_data: 6,
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
  review_rows: [
    {
      row: 12,
      business_name: "Synthetic Needs Review",
      compliance_status: "needs_review",
      eligible_channels: ["email"],
      needs_review_channels: ["sms", "whatsapp"],
      blocked_channels: [],
      invalid_channels: [],
      reason_codes: ["human_review_required:email"],
      explanation: "Needs review: a human decision and evidence are required.",
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
    mocks.downloadImportTemplate.mockReset();
    mocks.importLeads.mockReset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("starts with nothing to import", () => {
    renderScreen();

    expect(screen.getByRole("button", { name: "Import leads" })).toHaveProperty(
      "disabled",
      true,
    );
    expect(screen.queryByText(/rows read/i)).toBeNull();
  });

  it("lets an experienced user skip the guide trail", () => {
    renderScreen();

    expect(
      screen.getByRole("list", { name: "Wadi lead trail" }),
    ).toBeTruthy();
    expect(screen.getByText("Take the map")).toBeTruthy();
    expect(screen.getByText("Mark the trail")).toBeTruthy();
    expect(screen.getByText("Send the scout")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "I already have my CSV" }));

    expect(screen.getByText("Using your own CSV")).toBeTruthy();
    expect(screen.getByRole("button", { name: "I already have my CSV" })).toHaveProperty(
      "disabled",
      true,
    );
    expect(screen.getByRole("group", { name: "CSV drop area" })).toHaveFocus();
  });

  it("marks the first checkpoint after the CSV template downloads", async () => {
    mocks.downloadImportTemplate.mockResolvedValue(
      new Blob(["Business,Phone,Source\n"], { type: "text/csv" }),
    );
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    vi.stubGlobal("URL", {
      createObjectURL: vi.fn(() => "blob:template"),
      revokeObjectURL: vi.fn(),
    });

    renderScreen();
    fireEvent.click(screen.getByRole("button", { name: "Download CSV template" }));

    expect((await screen.findAllByText(/Map secured/)).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Download again" })).toBeTruthy();
  });

  it("marks the second checkpoint and lets the user replace a wrong file", () => {
    renderScreen();
    chooseFile();

    expect(screen.getAllByText(/Trail marked/).length).toBeGreaterThan(0);
    expect(screen.getByText(/webloom-lead-list.csv/)).toBeTruthy();
    expect(screen.getByText("Using your own CSV")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Wrong file?" }));

    expect(screen.queryByText(/webloom-lead-list.csv/)).toBeNull();
    expect(screen.getByRole("button", { name: "Import leads" })).toHaveProperty(
      "disabled",
      true,
    );
  });

  it("accepts a CSV dropped onto the trail marker", () => {
    renderScreen();
    const file = new File(["Business\n"], "dropped-leads.csv", { type: "text/csv" });

    fireEvent.drop(screen.getByRole("group", { name: "CSV drop area" }), {
      dataTransfer: { files: [file] },
    });

    expect(screen.getAllByText(/Trail marked/).length).toBeGreaterThan(0);
    expect(screen.getByText(/dropped-leads.csv/)).toBeTruthy();
  });

  it("explains the CSV columns and downloads the importer-compatible template", async () => {
    mocks.downloadImportTemplate.mockResolvedValue(
      new Blob(["Business,Phone,Source\n"], { type: "text/csv" }),
    );
    const createObjectUrl = vi.fn(() => "blob:template");
    const revokeObjectUrl = vi.fn();
    const anchorClick = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);
    vi.stubGlobal("URL", { createObjectURL: createObjectUrl, revokeObjectURL: revokeObjectUrl });

    renderScreen();

    expect(screen.getByRole("heading", { name: "Wadi’s Lead Trail" })).toBeTruthy();
    expect(screen.getByText("First, take the map.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Open trail notes" }));
    const dialog = screen.getByRole("dialog", { name: "Trail notes" });
    expect(within(dialog).getByText(/required columns/i)).toBeTruthy();
    for (const column of [
      "Business",
      "Sector",
      "Area",
      "Phone",
      "WhatsApp capable",
      "Website status",
      "Source",
    ]) {
      expect(within(dialog).getByText(column, { selector: "code" })).toBeTruthy();
    }
    expect(within(dialog).getByText(/optional columns/i)).toBeTruthy();
    for (const column of [
      "Email",
      "Contact name",
      "Contact type",
      "Source URL",
      "Collection date",
      "Collection method",
      "Intended purpose",
    ]) {
      expect(within(dialog).getByText(column, { selector: "code" })).toBeTruthy();
    }
    fireEvent.click(within(dialog).getByRole("button", { name: "Close" }));
    fireEvent.click(screen.getByRole("button", { name: "Download CSV template" }));

    await waitFor(() => expect(mocks.downloadImportTemplate).toHaveBeenCalledTimes(1));
    expect(createObjectUrl).toHaveBeenCalledTimes(1);
    expect(revokeObjectUrl).toHaveBeenCalledWith("blob:template");
    anchorClick.mockRestore();
    vi.unstubAllGlobals();
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
    fireEvent.click(screen.getByRole("button", { name: "Import leads" }));

    // Wait for the summary; while the upload runs there is a different status.
    await screen.findByText("Refused rows");
    const counts = screen
      .getAllByRole("status")
      .map((element) => element.textContent ?? "")
      .join(" ");
    expect(counts).toContain("52 rows read");
    expect(counts).toContain("50 created");
    expect(counts).toContain("2 refused");
    expect(counts).toContain("1 matched existing");
    expect(counts).toContain("1 duplicate");
    expect(screen.getAllByText("Needs review").length).toBeGreaterThan(0);
    expect(screen.getByText(/4 saved leads have incomplete source/i)).toBeTruthy();
    expect(screen.getByText("Automatically eligible")).toBeTruthy();
    expect(screen.getByText("Exception review")).toBeTruthy();
    expect(screen.getByText("Suppressed contacts")).toBeTruthy();
    expect(screen.getByText("Incomplete data")).toBeTruthy();
    expect(screen.getByText(/SMS, WHATSAPP still need review/i)).toBeTruthy();
    expect(
      screen.getByRole("link", { name: "Review exceptions" }).getAttribute("href"),
    ).toContain("exception_review=true");

    expect(screen.getByText("Mwangaza Hardware")).toBeTruthy();
    expect(screen.getByText("This phone number is already on row 3 of the file.")).toBeTruthy();
    expect(screen.getByText("Riverside Dental")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Download refused rows" })).toBeTruthy();
    expect(
      screen.getByText("Website status kept as written; has_website left false."),
    ).toBeTruthy();
  });

  it("celebrates a completed trail and starts a fresh import", async () => {
    mocks.importLeads.mockResolvedValue(summary);

    renderScreen();
    chooseFile();
    fireEvent.click(screen.getByRole("button", { name: "Import leads" }));

    expect(await screen.findByText("The scout is back.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Import another trail" }));

    expect(screen.queryByText(/rows read/i)).toBeNull();
    expect(screen.queryByText("The scout is back.")).toBeNull();
    expect(screen.getByRole("button", { name: "Import leads" })).toHaveProperty(
      "disabled",
      true,
    );
  });

  it("shows the server's reason when the file is refused", async () => {
    mocks.importLeads.mockRejectedValue(
      new Error("The file is missing these columns: Phone."),
    );

    renderScreen();
    chooseFile();
    fireEvent.click(screen.getByRole("button", { name: "Import leads" }));

    expect(await screen.findByRole("alert")).toHaveProperty(
      "textContent",
      "The file is missing these columns: Phone.",
    );
  });

  it("keeps the file and retries after a failed import", async () => {
    mocks.importLeads
      .mockRejectedValueOnce(new Error("The file is missing these columns: Phone."))
      .mockResolvedValueOnce(summary);

    renderScreen();
    chooseFile();
    fireEvent.click(screen.getByRole("button", { name: "Import leads" }));

    const dialog = await screen.findByRole("dialog", { name: "Wrong turn" });
    expect(dialog).toHaveProperty(
      "textContent",
      expect.stringContaining("The file is missing these columns: Phone."),
    );
    expect(dialog.textContent).toContain("webloom-lead-list.csv");

    fireEvent.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByText("The scout is back.")).toBeTruthy();
    expect(mocks.importLeads).toHaveBeenCalledTimes(2);
  });

  it("offers a retry when the template download fails", async () => {
    mocks.downloadImportTemplate.mockRejectedValue(
      new Error("Could not download the CSV template."),
    );

    renderScreen();
    fireEvent.click(screen.getByRole("button", { name: "Download CSV template" }));

    const dialog = await screen.findByRole("dialog", { name: "Wrong turn" });
    expect(dialog.textContent).toContain("Could not download the CSV template.");
    expect(within(dialog).getByRole("button", { name: "Try again" })).toBeTruthy();
  });
});
