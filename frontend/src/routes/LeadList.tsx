import { SlidersHorizontal } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { getLeadFilterOptions, listLeads } from "@/api/leads";
import type {
  ComplianceStatus,
  DataQualityStatus,
  LeadFilterOptions,
  LeadListParams,
  LeadListResponse,
  LeadStatus,
  Loaded,
} from "@/api/types";
import { DataSourceBanner } from "@/components/DataSourceBanner";
import { Scout } from "@/components/Scout";
import { ComplianceStatusBadge } from "@/components/compliance/ComplianceStatusBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useMediaQuery } from "@/lib/use-media-query";
import { cn } from "@/lib/utils";

const ANY = "all";
const PAGE_SIZE = 25;

const STATUS_LABELS: Record<LeadStatus, string> = {
  new: "New",
  contacted: "Contacted",
  replied: "Replied",
  qualified: "Qualified",
  handed_off: "Handed off",
  proposal: "Proposal",
  won: "Won",
  lost: "Lost",
  no_response: "No response",
  not_interested: "Not interested",
  opted_out: "Opted out",
};

const COMPLIANCE_LABELS: Record<ComplianceStatus, string> = {
  eligible: "Eligible",
  needs_review: "Needs review",
  blocked: "Blocked / suppressed",
  invalid: "Invalid / incomplete",
};

const QUALITY_LABELS: Record<DataQualityStatus, string> = {
  complete: "Complete data",
  incomplete: "Incomplete data",
  invalid: "Invalid data",
};

function cleanParam(value: string | null): string {
  return value ?? "";
}

export function LeadList() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [response, setResponse] = useState<Loaded<LeadListResponse> | null>(null);
  const [options, setOptions] = useState<LeadFilterOptions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const showLeadTable = useMediaQuery("(min-width: 768px)");

  const query = cleanParam(searchParams.get("q"));
  const sector = cleanParam(searchParams.get("sector"));
  const area = cleanParam(searchParams.get("area"));
  const source = cleanParam(searchParams.get("source"));
  const website = cleanParam(searchParams.get("website"));
  const status = cleanParam(searchParams.get("status"));
  const complianceStatus = cleanParam(searchParams.get("compliance_status"));
  const dataQuality = cleanParam(searchParams.get("data_quality_status"));
  const provenance = cleanParam(searchParams.get("provenance"));
  const outreachReady = cleanParam(searchParams.get("outreach_ready"));
  const exceptionReview = cleanParam(searchParams.get("exception_review"));
  const hasSuppression = cleanParam(searchParams.get("has_suppression"));
  const batchId = cleanParam(searchParams.get("batch_id"));
  const sort = cleanParam(searchParams.get("sort")) || "newest";
  const requestedPage = Number(searchParams.get("page") ?? "1");
  const page = Math.max(1, Number.isFinite(requestedPage) ? Math.floor(requestedPage) : 1);

  const filterValues = [
    query,
    sector,
    area,
    source,
    website,
    status,
    complianceStatus,
    dataQuality,
    provenance,
    outreachReady,
    exceptionReview,
    hasSuppression,
    batchId,
  ];
  const hasFilter = filterValues.some(Boolean);
  const activeFilterCount = filterValues.filter(Boolean).length;

  useEffect(() => {
    let cancelled = false;
    getLeadFilterOptions().then((loaded) => {
      if (!cancelled) setOptions(loaded.data);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const params: LeadListParams = {
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
      sort: sort as LeadListParams["sort"],
      q: query || undefined,
      sector: sector || undefined,
      area: area || undefined,
      source: source || undefined,
      website: (website || undefined) as "yes" | "no" | undefined,
      status: (status || undefined) as LeadStatus | undefined,
      compliance_status: (complianceStatus || undefined) as ComplianceStatus | undefined,
      data_quality_status: (dataQuality || undefined) as DataQualityStatus | undefined,
      provenance: (provenance || undefined) as LeadListParams["provenance"],
      outreach_ready:
        outreachReady === "yes" ? true : outreachReady === "no" ? false : undefined,
      exception_review:
        exceptionReview === "true" ? true : exceptionReview === "false" ? false : undefined,
      has_suppression:
        hasSuppression === "yes" ? true : hasSuppression === "no" ? false : undefined,
      batch_id: batchId || undefined,
    };
    listLeads(params)
      .then((loaded) => {
        if (!cancelled) {
          setResponse(loaded);
          setError(null);
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "Could not load leads");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [
    area,
    batchId,
    complianceStatus,
    dataQuality,
    exceptionReview,
    hasSuppression,
    outreachReady,
    page,
    provenance,
    query,
    sector,
    sort,
    source,
    status,
    website,
  ]);

  const total = response?.data.total ?? 0;
  const leads = response?.data.items ?? null;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const visiblePage = Math.min(page, pageCount);

  function setParam(key: string, value: string) {
    setError(null);
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "page") next.delete("page");
    setSearchParams(next, { replace: true });
  }

  function selectParam(key: string, value: string) {
    setParam(key, value === ANY ? "" : value);
  }

  function clearFilters() {
    setError(null);
    setSearchParams(new URLSearchParams(), { replace: true });
  }

  return (
    <div className="space-y-5">
      {response && <DataSourceBanner source={response.source} reason={response.reason} />}

      <Card>
        <CardHeader>
          <CardTitle>Leads</CardTitle>
          <CardDescription>
            {!response
              ? "Loading leads…"
              : hasFilter
                ? `${total} match the current filters`
                : `${total} in the pipeline`}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Input
                type="search"
                aria-label="Search leads"
                placeholder="Search business, phone, area"
                value={query}
                onChange={(event) => setParam("q", event.target.value)}
                className="h-9 min-w-0 flex-1"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="shrink-0 md:hidden"
                aria-expanded={filtersOpen}
                aria-controls="lead-filters"
                aria-label={
                  activeFilterCount > 0
                    ? `Filters, ${activeFilterCount} active`
                    : "Filters"
                }
                onClick={() => setFiltersOpen((open) => !open)}
              >
                <SlidersHorizontal className="size-4" />
                <span className="hidden sm:inline">Filters</span>
              </Button>
            </div>

            <div
              id="lead-filters"
              className={cn(
                "grid gap-2 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4",
                filtersOpen ? "grid" : "hidden md:grid",
              )}
            >
              <Select value={sector || ANY} onValueChange={(value) => selectParam("sector", value)}>
                <SelectTrigger aria-label="Filter by sector" className="h-9 w-full min-w-0">
                  <SelectValue placeholder="Sector" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ANY}>All sectors</SelectItem>
                  {(options?.sectors ?? []).map((value) => (
                    <SelectItem key={value} value={value}>{value}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={area || ANY} onValueChange={(value) => selectParam("area", value)}>
                <SelectTrigger aria-label="Filter by area" className="h-9 w-full min-w-0">
                  <SelectValue placeholder="Area" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ANY}>All areas</SelectItem>
                  {(options?.areas ?? []).map((value) => (
                    <SelectItem key={value} value={value}>{value}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={complianceStatus || ANY}
                onValueChange={(value) => selectParam("compliance_status", value)}
              >
                <SelectTrigger
                  aria-label="Filter by compliance status"
                  className="h-9 w-full min-w-0"
                >
                  <SelectValue placeholder="Compliance" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ANY}>Any compliance</SelectItem>
                  {(Object.keys(COMPLIANCE_LABELS) as ComplianceStatus[]).map((value) => (
                    <SelectItem key={value} value={value}>{COMPLIANCE_LABELS[value]}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={dataQuality || ANY}
                onValueChange={(value) => selectParam("data_quality_status", value)}
              >
                <SelectTrigger aria-label="Filter by data quality" className="h-9 w-full min-w-0">
                  <SelectValue placeholder="Data quality" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ANY}>Any data quality</SelectItem>
                  {(Object.keys(QUALITY_LABELS) as DataQualityStatus[]).map((value) => (
                    <SelectItem key={value} value={value}>{QUALITY_LABELS[value]}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={provenance || ANY} onValueChange={(value) => selectParam("provenance", value)}>
                <SelectTrigger aria-label="Filter by provenance" className="h-9 w-full min-w-0">
                  <SelectValue placeholder="Provenance" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ANY}>Any provenance</SelectItem>
                  <SelectItem value="available">Source available</SelectItem>
                  <SelectItem value="missing">Source missing</SelectItem>
                  <SelectItem value="incomplete">Source incomplete</SelectItem>
                </SelectContent>
              </Select>

              <Select value={outreachReady || ANY} onValueChange={(value) => selectParam("outreach_ready", value)}>
                <SelectTrigger aria-label="Filter by outreach readiness" className="h-9 w-full min-w-0">
                  <SelectValue placeholder="Outreach" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ANY}>Any readiness</SelectItem>
                  <SelectItem value="yes">Ready for outreach</SelectItem>
                  <SelectItem value="no">Not ready</SelectItem>
                </SelectContent>
              </Select>

              <Select value={exceptionReview || ANY} onValueChange={(value) => selectParam("exception_review", value)}>
                <SelectTrigger aria-label="Filter by exception review" className="h-9 w-full min-w-0">
                  <SelectValue placeholder="Exception review" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ANY}>Any exceptions</SelectItem>
                  <SelectItem value="true">Needs exception review</SelectItem>
                  <SelectItem value="false">No exception review</SelectItem>
                </SelectContent>
              </Select>

              <Select value={hasSuppression || ANY} onValueChange={(value) => selectParam("has_suppression", value)}>
                <SelectTrigger aria-label="Filter by suppression" className="h-9 w-full min-w-0">
                  <SelectValue placeholder="Suppression" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ANY}>Any restriction</SelectItem>
                  <SelectItem value="yes">Has restriction</SelectItem>
                  <SelectItem value="no">No restriction</SelectItem>
                </SelectContent>
              </Select>

              <Select value={website || ANY} onValueChange={(value) => selectParam("website", value)}>
                <SelectTrigger aria-label="Filter by website" className="h-9 w-full min-w-0">
                  <SelectValue placeholder="Website" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ANY}>Any website</SelectItem>
                  <SelectItem value="no">No website</SelectItem>
                  <SelectItem value="yes">Has website</SelectItem>
                </SelectContent>
              </Select>

              <Select value={status || ANY} onValueChange={(value) => selectParam("status", value)}>
                <SelectTrigger aria-label="Filter by status" className="h-9 w-full min-w-0">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ANY}>Any status</SelectItem>
                  {(options?.statuses ?? []).map((value) => (
                    <SelectItem key={value} value={value}>{STATUS_LABELS[value]}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={source || ANY} onValueChange={(value) => selectParam("source", value)}>
                <SelectTrigger aria-label="Filter by source" className="h-9 w-full min-w-0">
                  <SelectValue placeholder="Source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ANY}>Any source</SelectItem>
                  {(options?.sources ?? []).map((value) => (
                    <SelectItem key={value} value={value}>{value}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={batchId || ANY} onValueChange={(value) => selectParam("batch_id", value)}>
                <SelectTrigger aria-label="Filter by import batch" className="h-9 w-full min-w-0">
                  <SelectValue placeholder="Import batch" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ANY}>Any import batch</SelectItem>
                  {(options?.import_batches ?? []).map((batch) => (
                    <SelectItem key={batch.id} value={batch.id}>{batch.filename}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={sort} onValueChange={(value) => selectParam("sort", value === "newest" ? "" : value)}>
                <SelectTrigger aria-label="Sort leads" className="h-9 w-full min-w-0">
                  <SelectValue placeholder="Sort" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="newest">Newest first</SelectItem>
                  <SelectItem value="oldest">Oldest first</SelectItem>
                  <SelectItem value="business_name">Business name</SelectItem>
                  <SelectItem value="compliance_status">Compliance priority</SelectItem>
                </SelectContent>
              </Select>

              {hasFilter && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="justify-self-start"
                  onClick={clearFilters}
                >
                  Clear
                </Button>
              )}
            </div>
          </div>

          {error && (
            <p role="alert" className="text-sm text-destructive">{error}</p>
          )}

          {!error && !leads && (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, index) => (
                <Skeleton key={index} className="h-10 w-full" />
              ))}
            </div>
          )}

          {!error && leads && total === 0 && (
            <div className="flex items-center gap-3 rounded-lg border border-dashed border-border px-4 py-6">
              <Scout size={54} />
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">
                  {hasFilter ? "Nothing down this path." : "Nothing here yet. Import your list and the scout will get to work."}
                </p>
                {hasFilter && (
                  <Button variant="link" size="sm" className="h-auto p-0" onClick={clearFilters}>
                    Clear the filters
                  </Button>
                )}
              </div>
            </div>
          )}

          {!error && leads && leads.length > 0 && (
            <>
              {!showLeadTable && <ul className="space-y-2">
                {leads.map((lead) => (
                  <li key={lead.id}>
                    <Link
                      to={`/leads/${lead.id}`}
                      className="block rounded-xl border border-border bg-card p-4 transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="font-medium leading-snug">{lead.business_name}</p>
                          <p className="mt-1 truncate text-xs text-muted-foreground">
                            {lead.email ?? lead.phone ?? "No contact"}
                          </p>
                        </div>
                        <StatusBadge status={lead.status} />
                      </div>
                      <div className="mt-3 space-y-1.5 border-t border-border pt-3">
                        <ComplianceStatusBadge status={lead.compliance.status} />
                        <p className="line-clamp-3 text-xs leading-relaxed text-muted-foreground">
                          {lead.compliance.explanation}
                        </p>
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>}

              {showLeadTable && <div>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Business</TableHead>
                      <TableHead className="hidden lg:table-cell">Sector</TableHead>
                      <TableHead className="hidden lg:table-cell">Area</TableHead>
                      <TableHead className="hidden xl:table-cell">Phone</TableHead>
                      <TableHead>Compliance</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {leads.map((lead) => (
                      <TableRow
                        key={lead.id}
                        tabIndex={0}
                        role="link"
                        className="cursor-pointer align-top"
                        onClick={() => navigate(`/leads/${lead.id}`)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter") navigate(`/leads/${lead.id}`);
                        }}
                      >
                        <TableCell className="max-w-[260px] font-medium">
                          <span className="block truncate">{lead.business_name}</span>
                          <span className="mt-1 block truncate text-xs font-normal text-muted-foreground">
                            {lead.email ?? lead.phone ?? "No contact"}
                          </span>
                        </TableCell>
                        <TableCell className="hidden max-w-[150px] truncate lg:table-cell">
                          {lead.sector ?? "—"}
                        </TableCell>
                        <TableCell className="hidden max-w-[150px] truncate lg:table-cell">
                          {lead.area ?? "—"}
                        </TableCell>
                        <TableCell className="hidden font-mono text-xs whitespace-nowrap xl:table-cell">
                          {lead.phone ?? "—"}
                        </TableCell>
                        <TableCell className="max-w-[300px]">
                          <ComplianceStatusBadge status={lead.compliance.status} />
                          <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                            {lead.compliance.explanation}
                          </p>
                        </TableCell>
                        <TableCell><StatusBadge status={lead.status} /></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>}

              {total > PAGE_SIZE && (
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border pt-3">
                  <p className="text-xs text-muted-foreground">
                    Showing {(visiblePage - 1) * PAGE_SIZE + 1}–
                    {Math.min(visiblePage * PAGE_SIZE, total)} of {total}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={visiblePage <= 1}
                      onClick={() => setParam("page", String(visiblePage - 1))}
                    >
                      Previous
                    </Button>
                    <span className="text-xs text-muted-foreground">
                      Page {visiblePage} of {pageCount}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={visiblePage >= pageCount}
                      onClick={() => setParam("page", String(visiblePage + 1))}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
