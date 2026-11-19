import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getLead } from "@/api/leads";
import type { LeadDetail as LeadDetailRecord, Loaded } from "@/api/types";
import { CompliancePanel } from "@/components/compliance/CompliancePanel";
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

const SELLER_ACTIVITY_FIELDS = new Set([
  "channel",
  "previous_state",
  "new_state",
  "status",
  "eligible_channels",
  "suppressed_channels",
  "scope",
  "reason",
]);

function primitiveDetails(details: Record<string, unknown> | null) {
  return Object.entries(details ?? {}).filter(([, value]) => {
    return (
      typeof value === "string" ||
      typeof value === "number" ||
      typeof value === "boolean" ||
      value === null ||
      (Array.isArray(value) &&
        value.every(
          (item) =>
            typeof item === "string" ||
            typeof item === "number" ||
            typeof item === "boolean",
        ))
    );
  });
}

function activityValue(value: unknown): string {
  if (value === null) return "—";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

function activityDetails(details: Record<string, unknown> | null) {
  const entries = primitiveDetails(details);
  return {
    seller: entries.filter(([key]) => SELLER_ACTIVITY_FIELDS.has(key)),
    technical: entries.filter(([key]) => !SELLER_ACTIVITY_FIELDS.has(key)),
  };
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
  const sampleMode = response?.source === "sample";

  function applyComplianceUpdate(updated: LeadDetailRecord) {
    if (!id) return;
    setState({ id, response: { source: "api", data: updated }, error: null });
  }

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
                <Field label="Email">
                  <span className="font-mono text-xs">{lead.email ?? "—"}</span>
                </Field>
                <Field label="WhatsApp">{lead.whatsapp_capable ? "Yes" : "No / call only"}</Field>
                <Field label="Website">
                  {lead.website_presence === "has_website"
                    ? "Has a website"
                    : lead.website_presence === "no_website"
                      ? "No website"
                      : "Not checked / unknown"}
                </Field>
                <Field label="Research note">{lead.website_status ?? "—"}</Field>
                <Field label="Source">{lead.source}</Field>
                <Field label="Added">{new Date(lead.created_at).toLocaleDateString()}</Field>
              </dl>
            </CardContent>
          </Card>

          <CompliancePanel
            lead={lead}
            sampleMode={sampleMode}
            onUpdated={applyComplianceUpdate}
          />

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
                      {activityDetails(entry.details).seller.length > 0 && (
                        <dl
                          aria-label="Activity details"
                          className="grid gap-x-4 gap-y-1 text-xs sm:grid-cols-2"
                        >
                          {activityDetails(entry.details).seller.map(([key, value]) => (
                            <div key={key} className="flex gap-1">
                              <dt className="text-muted-foreground">{key}:</dt>
                              <dd>{activityValue(value)}</dd>
                            </div>
                          ))}
                        </dl>
                      )}
                      {activityDetails(entry.details).technical.length > 0 && (
                        <details
                          aria-label="Activity details"
                          className="rounded-md border border-border bg-muted/20 px-3 py-2 text-xs"
                        >
                          <summary className="cursor-pointer text-muted-foreground">
                            Technical details
                          </summary>
                          <dl className="mt-2 space-y-2">
                            {activityDetails(entry.details).technical.map(([key, value]) => (
                              <div key={key}>
                                <dt className="text-muted-foreground">{key}:</dt>
                                <dd className="break-all whitespace-pre-wrap font-mono">
                                  {activityValue(value)}
                                </dd>
                              </div>
                            ))}
                          </dl>
                        </details>
                      )}
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
