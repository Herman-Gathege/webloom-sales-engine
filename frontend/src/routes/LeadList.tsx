import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { listLeads } from "@/api/leads";
import type { LeadListResponse, Loaded } from "@/api/types";
import { DataSourceBanner } from "@/components/DataSourceBanner";
import { StatusBadge } from "@/components/StatusBadge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export function LeadList() {
  const navigate = useNavigate();
  const [response, setResponse] = useState<Loaded<LeadListResponse> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listLeads()
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

  const leads = response?.data.items ?? null;

  return (
    <div className="space-y-5">
      {response && <DataSourceBanner source={response.source} reason={response.reason} />}

      <Card>
        <CardHeader>
          <CardTitle>Leads</CardTitle>
          <CardDescription>
            {leads ? `${response?.data.total ?? leads.length} in the pipeline` : "Loading leads…"}
          </CardDescription>
        </CardHeader>
        <CardContent>
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

          {!error && leads && leads.length === 0 && (
            <p className="text-sm text-muted-foreground">No leads yet.</p>
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
