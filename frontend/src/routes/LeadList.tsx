import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { listLeads } from "@/api/leads";
import type { Lead, LeadListResponse, LeadStatus, Loaded } from "@/api/types";
import { DataSourceBanner } from "@/components/DataSourceBanner";
import { Scout } from "@/components/Scout";
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

/** Radix Select cannot hold an empty string, so "no filter" gets its own value. */
const ANY = "all";

/**
 * The filters run in the browser, so we need the whole list to page through it.
 * 200 is the API's cap; past that, real server-side filtering is the next job.
 */
const MAX_LEADS = 200;
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

function valuesOf(leads: Lead[], pick: (lead: Lead) => string | null): string[] {
  const seen = new Set<string>();
  for (const lead of leads) {
    const value = pick(lead);
    if (value) seen.add(value);
  }
  return [...seen].sort((a, b) => a.localeCompare(b));
}

export function LeadList() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [response, setResponse] = useState<Loaded<LeadListResponse> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listLeads({ limit: MAX_LEADS })
      .then((loaded) => {
        if (!cancelled) setResponse(loaded);
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(cause instanceof Error ? cause.message : "Could not load leads");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const allLeads = response?.data.items ?? null;

  const query = searchParams.get("q") ?? "";
  const sector = searchParams.get("sector") ?? "";
  const area = searchParams.get("area") ?? "";
  const website = searchParams.get("website") ?? "";
  const status = searchParams.get("status") ?? "";
  const requestedPage = Number(searchParams.get("page") ?? "1");

  const hasFilter = Boolean(query || sector || area || website || status);

  const sectors = useMemo(() => (allLeads ? valuesOf(allLeads, (l) => l.sector) : []), [allLeads]);
  const areas = useMemo(() => (allLeads ? valuesOf(allLeads, (l) => l.area) : []), [allLeads]);
  const statuses = useMemo(
    () => (allLeads ? [...new Set(allLeads.map((l) => l.status))].sort() : []),
    [allLeads],
  );

  const filtered = useMemo(() => {
    if (!allLeads) return null;
    const needle = query.trim().toLowerCase();
    return allLeads.filter((lead) => {
      if (sector && lead.sector !== sector) return false;
      if (area && lead.area !== area) return false;
      if (website === "yes" && !lead.has_website) return false;
      if (website === "no" && lead.has_website) return false;
      if (status && lead.status !== status) return false;
      if (!needle) return true;
      return [lead.business_name, lead.phone ?? "", lead.area ?? ""].some((value) =>
        value.toLowerCase().includes(needle),
      );
    });
  }, [allLeads, query, sector, area, website, status]);

  const pageCount = filtered ? Math.max(1, Math.ceil(filtered.length / PAGE_SIZE)) : 1;
  const page = Math.min(
    Math.max(1, Number.isFinite(requestedPage) ? Math.floor(requestedPage) : 1),
    pageCount,
  );
  const start = (page - 1) * PAGE_SIZE;
  const visible = filtered ? filtered.slice(start, start + PAGE_SIZE) : null;

  function setParam(key: string, value: string) {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    // Any filter change starts again from the first page.
    if (key !== "page") next.delete("page");
    setSearchParams(next, { replace: true });
  }

  function setPage(value: number) {
    setParam("page", value > 1 ? String(value) : "");
  }

  function clearFilters() {
    setSearchParams(new URLSearchParams(), { replace: true });
  }

  return (
    <div className="space-y-5">
      {response && <DataSourceBanner source={response.source} reason={response.reason} />}

      <Card>
        <CardHeader>
          <CardTitle>Leads</CardTitle>
          <CardDescription>
            {filtered === null
              ? "Loading leads…"
              : hasFilter
                ? `Showing ${filtered.length} of ${allLeads?.length ?? 0}`
                : `${response?.data.total ?? filtered.length} in the pipeline`}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {allLeads && allLeads.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <Input
                type="search"
                aria-label="Search leads"
                placeholder="Search business, phone or area"
                value={query}
                onChange={(event) => setParam("q", event.target.value)}
                className="h-9 w-full sm:w-64"
              />

              <Select
                value={sector || ANY}
                onValueChange={(value) => setParam("sector", value === ANY ? "" : value)}
              >
                <SelectTrigger aria-label="Filter by sector" className="h-9 w-[calc(50%-0.25rem)] sm:w-[170px]">
                  <SelectValue placeholder="Sector" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ANY}>All sectors</SelectItem>
                  {sectors.map((value) => (
                    <SelectItem key={value} value={value}>
                      {value}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={area || ANY}
                onValueChange={(value) => setParam("area", value === ANY ? "" : value)}
              >
                <SelectTrigger aria-label="Filter by area" className="h-9 w-[calc(50%-0.25rem)] sm:w-[160px]">
                  <SelectValue placeholder="Area" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ANY}>All areas</SelectItem>
                  {areas.map((value) => (
                    <SelectItem key={value} value={value}>
                      {value}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={website || ANY}
                onValueChange={(value) => setParam("website", value === ANY ? "" : value)}
              >
                <SelectTrigger aria-label="Filter by website" className="h-9 w-[calc(50%-0.25rem)] sm:w-[160px]">
                  <SelectValue placeholder="Website" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ANY}>Any website</SelectItem>
                  <SelectItem value="no">No website</SelectItem>
                  <SelectItem value="yes">Has website</SelectItem>
                </SelectContent>
              </Select>

              <Select
                value={status || ANY}
                onValueChange={(value) => setParam("status", value === ANY ? "" : value)}
              >
                <SelectTrigger aria-label="Filter by status" className="h-9 w-[calc(50%-0.25rem)] sm:w-[150px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ANY}>Any status</SelectItem>
                  {statuses.map((value) => (
                    <SelectItem key={value} value={value}>
                      {STATUS_LABELS[value]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {hasFilter && (
                <Button variant="ghost" size="sm" onClick={clearFilters}>
                  Clear
                </Button>
              )}
            </div>
          )}

          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}

          {!error && !visible && (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, index) => (
                <Skeleton key={index} className="h-10 w-full" />
              ))}
            </div>
          )}

          {!error && visible && allLeads?.length === 0 && (
            <div className="flex items-center gap-3 rounded-lg border border-dashed border-border px-4 py-6">
              <Scout size={54} />
              <p className="text-sm text-muted-foreground">
                Nothing here yet. Import your list and the scout will get to work.
              </p>
            </div>
          )}

          {!error && visible && (allLeads?.length ?? 0) > 0 && visible.length === 0 && (
            <div className="flex items-center gap-3 rounded-lg border border-dashed border-border px-4 py-6">
              <Scout size={54} />
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Nothing down this path.</p>
                <Button variant="link" size="sm" className="h-auto p-0" onClick={clearFilters}>
                  Clear the filters
                </Button>
              </div>
            </div>
          )}

          {!error && visible && visible.length > 0 && (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Business</TableHead>
                    <TableHead className="hidden lg:table-cell">Sector</TableHead>
                    <TableHead className="hidden lg:table-cell">Area</TableHead>
                    <TableHead className="hidden xl:table-cell">Phone</TableHead>
                    <TableHead className="hidden sm:table-cell">Website</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {visible.map((lead) => (
                    <TableRow
                      key={lead.id}
                      tabIndex={0}
                      role="link"
                      className="cursor-pointer"
                      onClick={() => navigate(`/leads/${lead.id}`)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") navigate(`/leads/${lead.id}`);
                      }}
                    >
                      <TableCell className="max-w-[240px] truncate font-medium">
                        {lead.business_name}
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
                      <TableCell className="hidden sm:table-cell">
                        {lead.has_website ? "Yes" : "No website"}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={lead.status} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {filtered && filtered.length > PAGE_SIZE && (
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border pt-3">
                  <p className="text-xs text-muted-foreground">
                    Showing {start + 1}–{Math.min(start + PAGE_SIZE, filtered.length)} of{" "}
                    {filtered.length}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page <= 1}
                      onClick={() => setPage(page - 1)}
                    >
                      Previous
                    </Button>
                    <span className="text-xs text-muted-foreground">
                      Page {page} of {pageCount}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page >= pageCount}
                      onClick={() => setPage(page + 1)}
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
