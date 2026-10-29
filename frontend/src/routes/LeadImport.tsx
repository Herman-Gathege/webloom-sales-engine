import { useState } from "react";
import { Link } from "react-router-dom";

import { importLeads, rejectedRowsCsv } from "@/api/leads";
import type { ImportSummary } from "@/api/types";
import { Scout } from "@/components/Scout";
import { ComplianceStatusBadge } from "@/components/compliance/ComplianceStatusBadge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type Phase = "idle" | "uploading" | "working" | "done" | "error";

function fileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function LeadImport() {
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [percent, setPercent] = useState(0);
  const [summary, setSummary] = useState<ImportSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const busy = phase === "uploading" || phase === "working";
  const mood =
    busy
      ? "loading"
      : phase === "error"
        ? "error"
        : phase === "done" && summary && summary.accepted > 0
          ? "success"
          : "idle";

  function chooseFile(selected: File | null) {
    setFile(selected);
    setSummary(null);
    setError(null);
    setPhase("idle");
    setPercent(0);
  }

  async function handleImport() {
    if (!file) return;
    setPhase("uploading");
    setPercent(0);
    setSummary(null);
    setError(null);

    try {
      const result = await importLeads(file, (value) => {
        setPercent(value);
        if (value >= 100) setPhase("working");
      });
      setSummary(result);
      setPhase("done");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The import failed.");
      setPhase("error");
    }
  }

  function downloadReport() {
    if (!summary) return;
    const blob = new Blob([rejectedRowsCsv(summary)], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `refused-rows-${summary.filename.replace(/\.csv$/i, "")}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-5">
      <Card className="relative">
        {/* Wrapped because the scout's own stylesheet sets display, which would
            beat Tailwind's `hidden` on the SVG itself. */}
        <span className="pointer-events-none absolute top-6 right-6 hidden sm:block">
          <Scout mood={mood} size={78} />
        </span>
        <CardHeader className="sm:pr-24">
          <CardTitle>Import leads</CardTitle>
          <CardDescription>
            Upload the researched list as a UTF-8 CSV. Every good row is saved; every row that
            cannot be saved comes back with one reason.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <Input
              type="file"
              accept=".csv,text/csv"
              aria-label="Choose a CSV file to import"
              className="h-9 w-full cursor-pointer sm:w-80"
              disabled={busy}
              onChange={(event) => chooseFile(event.target.files?.[0] ?? null)}
            />
            <Button onClick={handleImport} disabled={!file || busy}>
              {busy ? "Importing…" : "Import"}
            </Button>
            {file && !busy && (
              <span className="text-xs text-muted-foreground">
                {file.name} · {fileSize(file.size)}
              </span>
            )}
          </div>

          {(phase === "uploading" || phase === "working") && (
            <div className="space-y-1" role="status" aria-live="polite">
              <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
                <div
                  className="h-full bg-primary transition-[width] duration-150"
                  style={{ width: `${phase === "working" ? 100 : percent}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                {phase === "working"
                  ? "Checking every row…"
                  : `Uploading… ${percent}%`}
              </p>
            </div>
          )}

          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}

          {summary && (
            <div className="space-y-4">
              <Separator />

              <div
                role="status"
                aria-live="polite"
                className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm"
              >
                <span>
                  <span className="font-medium">{summary.row_count}</span> rows read
                </span>
                <span className="text-emerald-700">
                  <span className="font-medium">{summary.created}</span> created
                </span>
                <span className={summary.rejected > 0 ? "text-amber-700" : "text-muted-foreground"}>
                  <span className="font-medium">{summary.rejected}</span> refused
                </span>
                <span className="text-muted-foreground">
                  <span className="font-medium">{summary.matched}</span> matched existing
                </span>
                <span className="text-muted-foreground">
                  <span className="font-medium">{summary.duplicates}</span> duplicate
                  {summary.duplicates === 1 ? "" : "s"} in upload
                </span>
                {summary.warnings.length > 0 && (
                  <span className="text-muted-foreground">
                    {summary.warnings.length} warning{summary.warnings.length === 1 ? "" : "s"}
                  </span>
                )}
              </div>

              <div className="grid gap-2 text-sm sm:grid-cols-4">
                <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3">
                  <p className="text-xs font-medium text-emerald-800">Eligible</p>
                  <p className="text-xl font-semibold text-emerald-900">{summary.eligible}</p>
                </div>
                <div className="rounded-md border border-amber-200 bg-amber-50 p-3">
                  <p className="text-xs font-medium text-amber-800">Needs review</p>
                  <p className="text-xl font-semibold text-amber-900">{summary.needs_review}</p>
                </div>
                <div className="rounded-md border border-red-200 bg-red-50 p-3">
                  <p className="text-xs font-medium text-red-800">Blocked / suppressed</p>
                  <p className="text-xl font-semibold text-red-900">{summary.blocked}</p>
                </div>
                <div className="rounded-md border bg-slate-50 p-3">
                  <p className="text-xs font-medium text-slate-700">Invalid / incomplete</p>
                  <p className="text-xl font-semibold text-slate-900">{summary.invalid}</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button asChild size="sm" variant={summary.eligible > 0 ? "default" : "outline"}>
                  <Link to={`/leads?batch_id=${summary.batch_id}&compliance_status=eligible`}>
                    View eligible leads
                  </Link>
                </Button>
                <Button asChild size="sm" variant="outline">
                  <Link to={`/leads?batch_id=${summary.batch_id}&compliance_status=needs_review`}>
                    Review exceptions
                  </Link>
                </Button>
                <Button asChild size="sm" variant="outline">
                  <Link to={`/leads?batch_id=${summary.batch_id}&compliance_status=blocked`}>
                    Inspect blocked
                  </Link>
                </Button>
                <Button asChild size="sm" variant="outline">
                  <Link to={`/leads?batch_id=${summary.batch_id}&compliance_status=invalid`}>
                    Correct invalid rows
                  </Link>
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={downloadReport}
                  disabled={summary.rejected === 0}
                >
                  Download refused rows
                </Button>
              </div>

              <p className="text-xs text-muted-foreground">
                {summary.provenance_incomplete} saved lead
                {summary.provenance_incomplete === 1 ? "" : "s"} have incomplete source
                or provenance.
              </p>

              {summary.review_rows.length > 0 && (
                <div className="space-y-2">
                  <h2 className="text-sm font-medium">Rows needing attention</h2>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-16">Row</TableHead>
                        <TableHead>Business</TableHead>
                        <TableHead>Outcome</TableHead>
                        <TableHead>Why</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {summary.review_rows.map((row) => (
                        <TableRow key={`${row.row}-${row.compliance_status}`}>
                          <TableCell className="font-mono text-xs">{row.row}</TableCell>
                          <TableCell className="font-medium">{row.business_name}</TableCell>
                          <TableCell>
                            <ComplianceStatusBadge status={row.compliance_status} />
                          </TableCell>
                          <TableCell className="text-sm">
                            {row.explanation}
                            <span className="mt-1 block font-mono text-[11px] text-muted-foreground">
                              {row.reason_codes.join(", ")}
                            </span>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              {summary.rejected > 0 && (
                <div className="space-y-2">
                  <h2 className="text-sm font-medium">Refused rows</h2>
                  <p className="text-xs text-muted-foreground">
                    The row number is the line in your file, counting the header as line 1.
                  </p>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-16">Row</TableHead>
                        <TableHead>Business</TableHead>
                        <TableHead>Why</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {summary.rejected_rows.map((row) => (
                        <TableRow key={`${row.row}-${row.code}`}>
                          <TableCell className="font-mono text-xs">{row.row}</TableCell>
                          <TableCell className="font-medium">
                            {row.business_name || "—"}
                          </TableCell>
                          <TableCell className="text-sm">{row.reason}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              {summary.warnings.length > 0 && (
                <div className="space-y-2">
                  <h2 className="text-sm font-medium">Warnings</h2>
                  <p className="text-xs text-muted-foreground">
                    These rows were imported. The value was kept as written.
                  </p>
                  <ul className="space-y-1 text-sm">
                    {summary.warnings.map((warning) => (
                      <li key={`${warning.row}-${warning.code}-${warning.field}`}>
                        <Badge variant="secondary" className="mr-2 font-mono text-[11px]">
                          row {warning.row}
                        </Badge>
                        {warning.message}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
