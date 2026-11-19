import { Check, Download, FileUp } from "lucide-react";
import { useRef, useState, type DragEvent } from "react";
import { Link } from "react-router-dom";

import { downloadImportTemplate, importLeads, rejectedRowsCsv } from "@/api/leads";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useMediaQuery } from "@/lib/use-media-query";

type Phase = "idle" | "uploading" | "working" | "done" | "error";

const REQUIRED_COLUMNS = [
  "Business",
  "Sector",
  "Area",
  "Phone",
  "WhatsApp capable",
  "Website status",
  "Source",
];

const OPTIONAL_COLUMNS = [
  "Email",
  "Contact name",
  "Contact type",
  "Source URL",
  "Collection date",
  "Collection method",
  "Intended purpose",
];

function fileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface TrailStopProps {
  number: number;
  title: string;
  description: string;
  complete: boolean;
  current: boolean;
}

function TrailStop({
  number,
  title,
  description,
  complete,
  current,
}: TrailStopProps) {
  return (
    <li
      aria-current={current ? "step" : undefined}
      className={[
        "flex gap-3 rounded-xl border p-3 transition-[border-color,background-color,box-shadow] duration-300",
        complete
          ? "border-emerald-200 bg-emerald-50/80"
          : current
            ? "border-primary/40 bg-background shadow-sm"
            : "border-border bg-background",
      ].join(" ")}
    >
      <span
        className={[
          "grid size-8 shrink-0 place-items-center rounded-full text-xs font-semibold transition-colors duration-300",
          complete
            ? "bg-emerald-600 text-white"
            : current
              ? "bg-primary text-primary-foreground ring-4 ring-primary/10"
              : "bg-secondary text-secondary-foreground",
        ].join(" ")}
      >
        {complete ? <Check className="size-4" aria-hidden="true" /> : number}
      </span>
      <span className="min-w-0">
        <span className="font-semibold leading-snug text-primary">{title}</span>
        <span className="mt-1 block text-sm leading-snug text-muted-foreground">
          {description}
        </span>
      </span>
    </li>
  );
}

function CompleteTrailMark() {
  return (
    <div aria-hidden="true" className="mt-3 flex items-center gap-1.5">
      {[0, 1, 2].map((stop) => (
        <span key={stop} className="flex items-center gap-1.5">
          <span
            className="grid size-5 place-items-center rounded-full bg-emerald-600 text-white motion-safe:animate-in motion-safe:zoom-in-50 motion-safe:fade-in-0 motion-safe:duration-300"
            style={{ animationDelay: `${stop * 80}ms` }}
          >
            <Check className="size-3" strokeWidth={3} />
          </span>
          {stop < 2 && (
            <span
              className="h-0.5 w-5 origin-left bg-emerald-400 motion-safe:animate-in motion-safe:fade-in-0 motion-safe:slide-in-from-left-1 motion-safe:duration-300"
              style={{ animationDelay: `${stop * 80 + 40}ms` }}
            />
          )}
        </span>
      ))}
      <span className="ml-1 text-xs font-medium text-emerald-800">
        Map · Trail · Scout
      </span>
    </div>
  );
}

export function LeadImport() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropAreaRef = useRef<HTMLDivElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [percent, setPercent] = useState(0);
  const [summary, setSummary] = useState<ImportSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [templateError, setTemplateError] = useState<string | null>(null);
  const [downloadingTemplate, setDownloadingTemplate] = useState(false);
  const [guideSkipped, setGuideSkipped] = useState(false);
  const [templateReady, setTemplateReady] = useState(false);
  const [guideOpen, setGuideOpen] = useState(false);
  const [dragging, setDragging] = useState(false);
  const showResultTables = useMediaQuery("(min-width: 768px)");

  const busy = phase === "uploading" || phase === "working";
  const trailReady = templateReady || guideSkipped;
  const mood =
    busy || downloadingTemplate
      ? "loading"
      : error || templateError
        ? "error"
        : file || trailReady || (phase === "done" && summary && summary.accepted > 0)
          ? "success"
          : "idle";

  function chooseFile(selected: File | null) {
    if (busy) return;
    setFile(selected);
    setSummary(null);
    setError(null);
    setPhase("idle");
    setPercent(0);
    setGuideSkipped(selected !== null && !templateReady);
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

  async function downloadTemplate() {
    setTemplateError(null);
    setDownloadingTemplate(true);
    try {
      const blob = await downloadImportTemplate();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "wadi-lead-import-template.csv";
      link.click();
      URL.revokeObjectURL(url);
      setTemplateReady(true);
    } catch (cause) {
      setTemplateError(
        cause instanceof Error ? cause.message : "Could not download the CSV template.",
      );
    } finally {
      setDownloadingTemplate(false);
    }
  }

  function resetTrail() {
    chooseFile(null);
    setGuideSkipped(false);
    setTemplateReady(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    const selected = event.dataTransfer.files?.[0] ?? null;
    if (selected) chooseFile(selected);
  }

  return (
    <div className="space-y-5">
      {phase === "done" && summary ? (
        <Card
          className="overflow-hidden border-emerald-200 bg-emerald-50/70 motion-safe:animate-in motion-safe:fade-in-0 motion-safe:slide-in-from-bottom-1 motion-safe:duration-300"
        >
          <CardContent className="flex flex-col items-start gap-5 pt-5 sm:flex-row sm:items-center">
            <Scout mood="success" size={96} />
            <div className="min-w-0 flex-1" role="status" aria-live="polite">
              <p className="text-xs font-medium tracking-[0.16em] text-emerald-800 uppercase">
                Trail complete
              </p>
              <h2 className="mt-1 text-xl font-semibold text-emerald-950">
                The scout is back.
              </h2>
              <p className="mt-1 max-w-2xl text-sm leading-relaxed text-emerald-900">
                {summary.created} new lead{summary.created === 1 ? "" : "s"} joined Wadi,
                and {summary.row_count} CSV row{summary.row_count === 1 ? " was" : "s were"}{" "}
                checked.
              </p>
              <CompleteTrailMark />
            </div>
            <Button type="button" variant="outline" onClick={resetTrail}>
              Import another trail
            </Button>
          </CardContent>
        </Card>
      ) : (
      <Card className="motion-safe:animate-in motion-safe:fade-in-0 motion-safe:slide-in-from-bottom-1 motion-safe:duration-300">
        <CardHeader>
          <CardTitle>Wadi’s Lead Trail</CardTitle>
          <CardDescription>
            Three quick stops from a fresh CSV to a checked lead list.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid items-center gap-4 rounded-xl bg-secondary/45 p-4 lg:grid-cols-[11rem_1fr]">
            <div className="flex min-w-0 items-center gap-3">
              <Scout mood={mood} size={88} />
              <div className="relative min-w-0 flex-1 rounded-xl border border-border bg-background px-3 py-2 text-sm leading-snug shadow-sm">
                <span className="absolute top-1/2 -left-1.5 size-3 -translate-y-1/2 rotate-45 border-b border-l border-border bg-background" />
                {file ? (
                  <>
                    <span className="block font-medium text-foreground">Trail marked.</span>
                    <span className="text-muted-foreground">Send the scout when ready.</span>
                  </>
                ) : trailReady ? (
                  <>
                    <span className="block font-medium text-foreground">Map secured.</span>
                    <span className="text-muted-foreground">Bring your completed CSV.</span>
                  </>
                ) : (
                  <>
                    <span className="block font-medium text-foreground">Start at the trailhead.</span>
                    <span className="text-muted-foreground">First, take the map.</span>
                  </>
                )}
              </div>
            </div>
            <ol
              aria-label="Wadi lead trail"
              className="grid gap-2 text-sm md:grid-cols-3"
            >
              <TrailStop
                number={1}
                title="Take the map"
                description={
                  guideSkipped
                    ? "Using your own CSV."
                    : templateReady
                      ? "Map secured. Download it again if needed."
                      : "Download Wadi’s CSV template."
                }
                complete={trailReady}
                current={!trailReady && !file}
              />
              <TrailStop
                number={2}
                title="Mark the trail"
                description={
                  file
                    ? "Trail marked. Your list is ready."
                    : "Add the researched rows to the template."
                }
                complete={file !== null}
                current={trailReady && !file}
              />
              <TrailStop
                number={3}
                title="Send the scout"
                description={
                  busy
                    ? "Reading every row now."
                    : file
                      ? "Import when you are ready."
                      : "Upload the completed UTF-8 CSV."
                }
                complete={phase === "done"}
                current={file !== null && !busy}
              />
            </ol>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              type="button"
              onClick={() => void downloadTemplate()}
              disabled={downloadingTemplate || busy}
            >
              <Download className="size-4" aria-hidden="true" />
              {downloadingTemplate
                ? "Downloading…"
                : templateReady
                  ? "Download again"
                  : "Download CSV template"}
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={guideSkipped}
              onClick={() => {
                setGuideSkipped(true);
                dropAreaRef.current?.focus();
              }}
            >
              I already have my CSV
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={() => setGuideOpen(true)}
            >
              Open trail notes
            </Button>
            {guideSkipped && (
              <span className="text-sm text-muted-foreground">Using your own CSV</span>
            )}
          </div>
        </CardContent>
      </Card>
      )}

      <span className="sr-only" role="status" aria-live="polite">
        {file
          ? "Trail marked. Your CSV is ready to import."
          : templateReady
            ? "Map secured. Download completed."
            : guideSkipped
              ? "Using your own CSV."
              : ""}
      </span>

      <Dialog open={guideOpen} onOpenChange={setGuideOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Trail notes</DialogTitle>
            <DialogDescription>
              Keep the column names exact, then upload the completed file as UTF-8 CSV.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
              <div>
                <p className="text-sm font-medium">Required columns</p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {REQUIRED_COLUMNS.map((column) => (
                    <code key={column} className="rounded bg-secondary px-2 py-1 text-xs">
                      {column}
                    </code>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-sm font-medium">Optional columns</p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {OPTIONAL_COLUMNS.map((column) => (
                    <code key={column} className="rounded border border-border px-2 py-1 text-xs">
                      {column}
                    </code>
                  ))}
                </div>
              </div>
              <div className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
                <p>
                  <span className="font-medium text-foreground">Phone:</span> use{" "}
                  <code>0700 000 000</code>, <code>020 000 0000</code>, or{" "}
                  <code>+254700000000</code>.
                </p>
                <p>
                  <span className="font-medium text-foreground">Dates:</span> use ISO format, such
                  as <code>2026-11-19</code>.
                </p>
                <p>
                  <span className="font-medium text-foreground">Source:</span> describe where the
                  business information came from.
                </p>
                <p>
                  <span className="font-medium text-foreground">WhatsApp capable:</span> use{" "}
                  <code>Yes</code> or <code>Call only</code>.
                </p>
                <p>
                  <span className="font-medium text-foreground">Contact type:</span> use{" "}
                  <code>unknown</code>, <code>generic_business</code>, or{" "}
                  <code>named_individual</code>.
                </p>
                <p>
                  <span className="font-medium text-foreground">Website status:</span> keep the
                  research wording, such as <code>no website listed</code> or{" "}
                  <code>Facebook page only</code>.
                </p>
              </div>
          </div>
        </DialogContent>
      </Dialog>

      <Card className="relative">
        <CardHeader>
          <CardTitle>{phase === "done" ? "Field report" : "Import leads"}</CardTitle>
          <CardDescription>
            {phase === "done"
              ? "Every row has an outcome. Follow the trail that matters next."
              : "Every good row is saved. Every row Wadi cannot use comes back with one plain reason."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {phase !== "done" && (
            <>
          <div
            ref={dropAreaRef}
            role="group"
            aria-label="CSV drop area"
            tabIndex={-1}
            className={[
              "relative rounded-xl border-2 border-dashed p-5 text-center transition-[border-color,background-color] duration-200 sm:p-6",
              dragging
                ? "border-primary bg-secondary"
                : file
                  ? "border-emerald-300 bg-emerald-50/60"
                : "border-border bg-secondary/30",
            ].join(" ")}
            onDragEnter={(event) => {
              event.preventDefault();
              if (!busy) setDragging(true);
            }}
            onDragOver={(event) => {
              event.preventDefault();
              if (!busy) setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
          >
            <Input
              ref={fileInputRef}
              type="file"
              accept=".csv,text/csv"
              aria-label="Choose a CSV file to import"
              className="sr-only"
              disabled={busy}
              onChange={(event) => chooseFile(event.target.files?.[0] ?? null)}
            />
            {file ? (
              <div className="flex flex-col items-center gap-3 text-center sm:flex-row sm:text-left">
                <span className="grid size-11 shrink-0 place-items-center rounded-full bg-emerald-600 text-white shadow-sm">
                  <Check className="size-5" aria-hidden="true" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-emerald-950">{file.name}</p>
                  <p className="mt-0.5 text-xs text-emerald-800">
                    {fileSize(file.size)} · Ready for the trail
                  </p>
                </div>
                {!busy && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      chooseFile(null);
                      if (fileInputRef.current) fileInputRef.current.value = "";
                    }}
                  >
                    Wrong file?
                  </Button>
                )}
              </div>
            ) : (
              <>
                <span className="mx-auto grid size-12 place-items-center rounded-full bg-background text-primary shadow-sm ring-1 ring-border">
                  <FileUp className="size-6" aria-hidden="true" />
                </span>
                <p className="mt-3 font-medium">
                  {dragging ? "Drop it here. Wadi will take it from here." : "Drop your CSV at the trailhead"}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  UTF-8 CSV up to the import limit
                </p>
                <Button
                  type="button"
                  variant="outline"
                  className="mt-3 bg-background"
                  disabled={busy}
                  onClick={() => fileInputRef.current?.click()}
                >
                  Choose a CSV
                </Button>
              </>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button type="button" onClick={handleImport} disabled={!file || busy}>
              {busy ? "Scout is moving…" : "Import leads"}
            </Button>
            {file && !busy && (
              <span className="text-sm text-muted-foreground">
                Wadi will check every row before saving anything.
              </span>
            )}
          </div>

          {(phase === "uploading" || phase === "working") && (
            <div className="space-y-2 rounded-xl border border-border bg-secondary/35 p-4">
              <div className="flex items-center justify-between gap-3 text-sm">
                <p className="font-medium">
                  {phase === "working" ? "Checking the trail" : "Following the trail"}
                </p>
                <p className="text-muted-foreground" aria-live="polite">
                  {phase === "working" ? "Final checks" : `${percent}%`}
                </p>
              </div>
              <div className="relative h-8 px-3">
                <div
                  role="progressbar"
                  aria-label="Lead import progress"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={phase === "working" ? 100 : percent}
                  className="absolute inset-x-3 top-1/2 h-2 -translate-y-1/2 overflow-hidden rounded-full bg-background ring-1 ring-border"
                >
                <div
                  className="h-full rounded-full bg-primary transition-[width] duration-150 motion-reduce:transition-none"
                  style={{ width: `${phase === "working" ? 100 : percent}%` }}
                />
              </div>
                <span
                  className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 transition-[left] duration-150 motion-reduce:transition-none"
                  style={{
                    left: `clamp(1rem, ${phase === "working" ? 100 : percent}%, calc(100% - 1rem))`,
                  }}
                >
                  <Scout mood="loading" size={30} />
                </span>
              </div>
              <p className="text-sm text-muted-foreground" role="status" aria-live="polite">
                {phase === "working"
                  ? "Wadi has the map. Checking every row now…"
                  : "Taking the CSV down the trail…"}
              </p>
            </div>
          )}
            </>
          )}

          {summary && (
            <div className="space-y-4">
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

              <div className="grid grid-cols-2 gap-2 text-sm lg:grid-cols-5">
                <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3">
                  <p className="text-xs font-medium text-emerald-800">
                    Automatically eligible
                  </p>
                  <p className="text-xl font-semibold text-emerald-900">
                    {summary.automated_eligible}
                  </p>
                </div>
                <div className="rounded-md border border-amber-200 bg-amber-50 p-3">
                  <p className="text-xs font-medium text-amber-800">Exception review</p>
                  <p className="text-xl font-semibold text-amber-900">
                    {summary.requiring_review}
                  </p>
                </div>
                <div className="rounded-md border border-red-200 bg-red-50 p-3">
                  <p className="text-xs font-medium text-red-800">Suppressed contacts</p>
                  <p className="text-xl font-semibold text-red-900">
                    {summary.suppressed_contacts}
                  </p>
                </div>
                <div className="rounded-md border bg-slate-50 p-3">
                  <p className="text-xs font-medium text-slate-700">Invalid</p>
                  <p className="text-xl font-semibold text-slate-900">{summary.invalid}</p>
                </div>
                <div className="rounded-md border bg-slate-50 p-3">
                  <p className="text-xs font-medium text-slate-700">Incomplete data</p>
                  <p className="text-xl font-semibold text-slate-900">
                    {summary.incomplete_data}
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button asChild size="sm" variant={summary.eligible > 0 ? "default" : "outline"}>
                  <Link to={`/leads?batch_id=${summary.batch_id}&compliance_status=eligible`}>
                    View eligible leads
                  </Link>
                </Button>
                <Button asChild size="sm" variant="outline">
                  <Link to={`/leads?batch_id=${summary.batch_id}&exception_review=true`}>
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
                  {!showResultTables && <ul className="space-y-2">
                    {summary.review_rows.map((row) => (
                      <li
                        key={`${row.row}-${row.compliance_status}`}
                        className="rounded-xl border border-border bg-card p-3"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="font-medium leading-snug">
                              {row.business_name || "Unnamed business"}
                            </p>
                            <p className="mt-1 text-xs text-muted-foreground">
                              CSV row {row.row}
                            </p>
                          </div>
                          <ComplianceStatusBadge status={row.compliance_status} />
                        </div>
                        <p className="mt-3 text-sm leading-relaxed">{row.explanation}</p>
                        {row.needs_review_channels.length > 0 && (
                          <p className="mt-2 text-sm font-medium text-amber-800">
                            {row.needs_review_channels
                              .map((channel) => channel.toUpperCase())
                              .join(", ")}{" "}
                            still need review.
                          </p>
                        )}
                        <p className="mt-2 break-words font-mono text-[11px] text-muted-foreground">
                          {row.reason_codes.join(", ")}
                        </p>
                      </li>
                    ))}
                  </ul>}
                  {showResultTables && <div>
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
                              {row.needs_review_channels.length > 0 && (
                                <span className="mt-1 block text-sm font-medium text-amber-800">
                                  {row.needs_review_channels
                                    .map((channel) => channel.toUpperCase())
                                    .join(", ")}{" "}
                                  still need review.
                                </span>
                              )}
                              <span className="mt-1 block font-mono text-[11px] text-muted-foreground">
                                {row.reason_codes.join(", ")}
                              </span>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>}
                </div>
              )}

              {summary.rejected > 0 && (
                <div className="space-y-2">
                  <h2 className="text-sm font-medium">Refused rows</h2>
                  <p className="text-xs text-muted-foreground">
                    The row number is the line in your file, counting the header as line 1.
                  </p>
                  {!showResultTables && <ul className="space-y-2">
                    {summary.rejected_rows.map((row) => (
                      <li
                        key={`${row.row}-${row.code}`}
                        className="rounded-xl border border-border bg-card p-3"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <p className="font-medium">{row.business_name || "Unnamed row"}</p>
                          <Badge variant="secondary" className="shrink-0 font-mono text-[11px]">
                            row {row.row}
                          </Badge>
                        </div>
                        <p className="mt-2 text-sm leading-relaxed">{row.reason}</p>
                      </li>
                    ))}
                  </ul>}
                  {showResultTables && <div>
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
                  </div>}
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

      <Dialog
        open={error !== null || templateError !== null}
        onOpenChange={(open) => {
          if (!open) {
            setError(null);
            setTemplateError(null);
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Wrong turn</DialogTitle>
            <DialogDescription>
              {templateError
                ? "The map could not be downloaded. Nothing else changed, so Wadi can try again."
                : "Wadi could not finish this import. Your selected file is still at the trailhead."}
            </DialogDescription>
          </DialogHeader>
          <div className="flex items-start gap-4 rounded-xl bg-secondary/60 p-4">
            <Scout mood="error" size={68} />
            <div className="min-w-0">
              <p className="text-sm font-medium">
                {templateError ? "CSV template" : file?.name ?? "Selected CSV"}
              </p>
              <p role="alert" className="mt-1 text-sm text-destructive">
                {error ?? templateError}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setError(null);
                setTemplateError(null);
              }}
            >
              Not now
            </Button>
            <Button
              type="button"
              onClick={() => {
                const retryImport = error !== null;
                setError(null);
                setTemplateError(null);
                if (retryImport) void handleImport();
                else void downloadTemplate();
              }}
            >
              Try again
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
