import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { listLeads } from "@/api/leads";
import type { Lead, LeadListResponse, LeadStatus, Loaded } from "@/api/types";
import { DataSourceBanner } from "@/components/DataSourceBanner";
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
    // The list is filtered in the browser this sprint, so load the whole list
    // the API will give us in one page. The API caps `limit` at 200.
    listLeads({ limit: 200 })
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

  const hasFilter = Boolean(query || sector || area || website || status);

  const sectors = useMemo(() => (allLeads ? valuesOf(allLeads, (l) => l.sector) : []), [allLeads]);
  const areas = useMemo(() => (allLeads ? valuesOf(allLeads, (l) => l.area) : []), [allLeads]);
  const statuses = useMemo(
    () => (allLeads ? [...new Set(allLeads.map((l) => l.status))].sort() : []),
    [allLeads],
  );

  const leads = useMemo(() => {
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

  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    setSearchParams(next, { replace: true });
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
            {leads === null
              ? "Loading leads…"
              : hasFilter
                ? `Showing ${leads.length} of ${allLeads?.length ?? 0} leads`
                : `${response?.data.total ?? leads.length} in the pipeline`}
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
                onChange={(event) => setFilter("q", event.target.value)}
                className="h-9 w-full sm:w-64"
              />

              <Select
                value={sector || ANY}
                onValueChange={(value) => setFilter("sector", value === ANY ? "" : value)}
              >
                <SelectTrigger aria-label="Filter by sector" className="h-9 w-[170px]">
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
                onValueChange={(value) => setFilter("area", value === ANY ? "" : value)}
              >
                <SelectTrigger aria-label="Filter by area" className="h-9 w-[160px]">
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
                onValueChange={(value) => setFilter("website", value === ANY ? "" : value)}
              >
                <SelectTrigger aria-label="Filter by website" className="h-9 w-[160px]">
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
                onValueChange={(value) => setFilter("status", value === ANY ? "" : value)}
              >
                <SelectTrigger aria-label="Filter by status" className="h-9 w-[150px]">
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

          {!error && !leads && (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, index) => (
                <Skeleton key={index} className="h-10 w-full" />
              ))}
            </div>
          )}

          {!error && leads && allLeads?.length === 0 && (
            <p className="text-sm text-muted-foreground">No leads yet.</p>
          )}

          {!error && leads && (allLeads?.length ?? 0) > 0 && leads.length === 0 && (
            <p className="text-sm text-muted-foreground">No leads match these filters.</p>
          )}

          {!error && leads && leads.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Business</TableHead>
                  <TableHead>Sector</TableHead>
                  <TableHead>Area</TableHead>
                  <TableHead>Phone</TableHead>
                  <TableHead>Website</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {leads.map((lead) => (
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
                    <TableCell className="font-medium">{lead.business_name}</TableCell>
                    <TableCell>{lead.sector ?? "—"}</TableCell>
                    <TableCell>{lead.area ?? "—"}</TableCell>
                    <TableCell className="font-mono text-xs whitespace-nowrap">
                      {lead.phone ?? "—"}
                    </TableCell>
                    <TableCell>{lead.has_website ? "Yes" : "No website"}</TableCell>
                    <TableCell>
                      <StatusBadge status={lead.status} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
