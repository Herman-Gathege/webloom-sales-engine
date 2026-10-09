import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getLead } from "@/api/leads";
import type { LeadDetail as LeadDetailRecord, Loaded } from "@/api/types";
import { DataSourceBanner } from "@/components/DataSourceBanner";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <dt className="text-xs tracking-wide text-muted-foreground uppercase">{label}</dt>
      <dd className="text-sm">{children}</dd>
    </div>
  );
}

export function LeadDetail() {
  const { id } = useParams<{ id: string }>();
  // The id travels with the result so switching leads never shows the previous
  // lead's data while the next one is loading — no reset inside the effect.
  const [state, setState] = useState<{
    id: string;
    response: Loaded<LeadDetailRecord> | null;
    error: string | null;
  }>({ id: "", response: null, error: null });

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    getLead(id)
      .then((loaded) => {
        if (!cancelled) setState({ id, response: loaded, error: null });
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setState({
            id,
            response: null,
            error: cause instanceof Error ? cause.message : "Could not load lead",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const settled = state.id === id;
  const response = settled ? state.response : null;
  const error = settled ? state.error : null;
  const lead = response?.data ?? null;

  return (
    <div className="space-y-5">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link to="/leads">← Back to leads</Link>
      </Button>

      {response && <DataSourceBanner source={response.source} reason={response.reason} />}

      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}

      {!error && !lead && (
        <div className="space-y-3">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-40 w-full" />
        </div>
      )}

      {!error && lead && (
        <div className="space-y-5">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">{lead.business_name}</h1>
            <StatusBadge status={lead.status} />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Details</CardTitle>
              <CardDescription>
                {lead.sector ?? "No sector"} · {lead.area ?? "No area"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <Field label="Phone">
                  <span className="font-mono text-xs">{lead.phone ?? "—"}</span>
                </Field>
                <Field label="WhatsApp">{lead.whatsapp_capable ? "Yes" : "No / call only"}</Field>
                <Field label="Website">{lead.has_website ? "Yes" : "None found"}</Field>
                <Field label="Research note">{lead.website_status ?? "—"}</Field>
                <Field label="Source">{lead.source}</Field>
                <Field label="Added">{new Date(lead.created_at).toLocaleDateString()}</Field>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Activity</CardTitle>
              <CardDescription>Everything that has happened to this lead so far.</CardDescription>
            </CardHeader>
            <CardContent>
              {lead.activity.length === 0 ? (
                <p className="text-sm text-muted-foreground">Nothing recorded yet.</p>
              ) : (
                <ol className="space-y-4">
                  {lead.activity.map((entry, index) => (
                    <li key={entry.id} className="space-y-2">
                      <div className="flex flex-wrap items-baseline justify-between gap-2">
                        <p className="text-sm">{entry.summary}</p>
                        <time
                          className="text-xs text-muted-foreground"
                          dateTime={entry.created_at}
                        >
                          {new Date(entry.created_at).toLocaleString()}
                        </time>
                      </div>
                      <p className="font-mono text-xs text-muted-foreground">
                        {entry.type} · {entry.actor}
                      </p>
                      {index < lead.activity.length - 1 && <Separator className="mt-2" />}
                    </li>
                  ))}
                </ol>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
