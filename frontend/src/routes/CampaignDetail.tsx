import { AlertTriangle, Archive, ArrowLeft, Pencil, RotateCcw, WandSparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  archiveCampaign,
  generateCampaign,
  getCampaign,
  restoreCampaign,
  type CampaignDetail as CampaignDetailRecord,
  type CampaignDraft,
  type CampaignSkip,
} from "@/api/campaign";
import { useAuth } from "@/auth/context";
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

export function CampaignDetail() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [campaign, setCampaign] = useState<CampaignDetailRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmGenerate, setConfirmGenerate] = useState(false);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    getCampaign(id)
      .then((result) => {
        if (!cancelled) {
          setCampaign(result);
          setError(null);
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "Could not load the campaign.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const canMutate = Boolean(
    campaign && user && (user.role === "admin" || user.id === campaign.owner_id),
  );

  async function run(action: () => Promise<CampaignDetailRecord>) {
    setBusy(true);
    setError(null);
    try {
      setCampaign(await action());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not update the campaign.");
    } finally {
      setBusy(false);
    }
  }

  if (!campaign && !error) {
    return <p className="text-sm text-muted-foreground">Loading campaign…</p>;
  }

  if (!campaign) {
    return <p role="alert" className="text-sm text-destructive">{error}</p>;
  }

  const skipGroups = groupSkips(campaign.skips);

  return (
    <div className="space-y-5">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link to="/campaigns"><ArrowLeft className="size-4" />Back to campaigns</Link>
      </Button>

      {error && <p role="alert" className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</p>}

      <Card>
        <CardHeader className="flex-row items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle>{campaign.name}</CardTitle>
              <CampaignStatus status={campaign.status} />
            </div>
            <CardDescription className="mt-2">{campaign.goal}</CardDescription>
          </div>
          {canMutate && (
            <div className="flex flex-wrap gap-2">
              {campaign.status === "draft" && (
                <>
                  <Button asChild size="sm" variant="outline">
                    <Link to={`/campaigns/${campaign.id}/edit`}><Pencil className="size-4" />Edit</Link>
                  </Button>
                  <Button size="sm" onClick={() => setConfirmGenerate(true)} disabled={busy}>
                    <WandSparkles className="size-4" />Generate drafts
                  </Button>
                </>
              )}
              {campaign.status !== "archived" ? (
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={busy}
                  onClick={() => id && void run(() => archiveCampaign(id))}
                >
                  <Archive className="size-4" />Archive
                </Button>
              ) : (
                <Button
                  size="sm"
                  variant="outline"
                  disabled={busy}
                  onClick={() => id && void run(() => restoreCampaign(id))}
                >
                  <RotateCcw className="size-4" />Restore
                </Button>
              )}
            </div>
          )}
        </CardHeader>
        <CardContent>
          <dl className="grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
            <Detail label="Offer" value={campaign.offer_name} />
            <Detail label="Template" value={campaign.template_name} />
            <Detail label="Channel" value={campaign.channel.toUpperCase()} />
            <Detail label="Owner" value={campaign.owner_email} />
            <Detail label="Selected" value={String(campaign.selected_count)} />
            <Detail label="Drafts" value={String(campaign.draft_count)} />
            <Detail label="Skipped" value={String(campaign.skip_count)} />
            <Detail
              label="Generated"
              value={campaign.generated_at ? new Date(campaign.generated_at).toLocaleString() : "Not yet"}
            />
          </dl>
          {Object.keys(campaign.selection_context).length > 0 && (
            <details className="mt-4 text-xs">
              <summary className="cursor-pointer text-muted-foreground">
                Selection context
              </summary>
              <dl className="mt-2 grid gap-2 sm:grid-cols-2">
                {Object.entries(campaign.selection_context).map(([key, value]) => (
                  <div key={key}>
                    <dt className="text-muted-foreground">{key.replaceAll("_", " ")}</dt>
                    <dd className="break-words font-medium">{String(value)}</dd>
                  </div>
                ))}
              </dl>
            </details>
          )}
        </CardContent>
      </Card>

      <Dialog open={confirmGenerate} onOpenChange={setConfirmGenerate}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Generate and freeze drafts?</DialogTitle>
            <DialogDescription>
              Wadi will recheck every selected lead and generate one draft per eligible lead.
              Drafts are labelled <strong>Not sent</strong>, cannot be edited or regenerated in
              Sprint 5, and skipped leads cannot be retried in this campaign.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-wrap gap-2">
            <Button
              disabled={busy}
              onClick={() => {
                if (!id) return;
                setConfirmGenerate(false);
                void run(() => generateCampaign(id));
              }}
            >
              {busy ? "Generating…" : "Generate drafts"}
            </Button>
            <Button variant="outline" onClick={() => setConfirmGenerate(false)}>Cancel</Button>
          </div>
        </DialogContent>
      </Dialog>

      {campaign.status === "draft" && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="flex items-start gap-3 p-4">
            <AlertTriangle className="size-5 shrink-0 text-amber-800" aria-hidden="true" />
            <div className="min-w-0">
              <p className="font-semibold text-amber-900">
                Campaign drafts are not sent automatically.
              </p>
              <p className="mt-1 text-sm text-amber-800">
                Preview is performed on the create/edit screen. Generation will recheck eligibility
                and prepare one immutable draft per eligible lead. Each draft is labelled{" "}
                <strong>Not sent</strong> and cannot be delivered until a person approves it.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {campaign.drafts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Drafts</CardTitle>
            <CardDescription>Immutable message snapshots. None of these messages has been sent.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 lg:grid-cols-2">
            {campaign.drafts.map((draft) => <DraftCard key={draft.id} draft={draft} />)}
          </CardContent>
        </Card>
      )}

      {campaign.skips.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Skipped leads</CardTitle>
            <CardDescription>These leads did not receive a draft.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(skipGroups).map(([label, rows]) => (
              <details key={label} className="rounded-lg border border-border p-3" open={Object.keys(skipGroups).length <= 3}>
                <summary className="cursor-pointer font-medium">{label} · {rows.length}</summary>
                <ul className="mt-3 space-y-2">
                  {rows.map((row) => (
                    <li key={row.lead_id} className="rounded-md bg-muted/40 p-3 text-sm">
                      <p className="font-medium">{row.business_name}</p>
                      <p className="mt-1 text-muted-foreground">{row.explanation}</p>
                      <details className="mt-2 text-xs">
                        <summary className="cursor-pointer text-muted-foreground">
                          Technical reason codes
                        </summary>
                        <p className="mt-1 break-all font-mono text-[11px] text-muted-foreground">
                          {row.reason_codes.join(", ")}
                        </p>
                      </details>
                    </li>
                  ))}
                </ul>
              </details>
            ))}
          </CardContent>
        </Card>
      )}

      {campaign.events.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Campaign history</CardTitle>
            <CardDescription>
              Append-only campaign actions retained with the archive.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ol className="space-y-2 text-sm">
              {campaign.events.map((event, index) => (
                <li
                  key={`${event.event_type}-${event.created_at}-${index}`}
                  className="rounded-md border border-border p-3"
                >
                  <p className="font-medium">
                    {event.event_type.replaceAll(".", " · ")}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {event.actor_email ?? "system"} ·{" "}
                    {new Date(event.created_at).toLocaleString()}
                  </p>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function DraftCard({ draft }: { draft: CampaignDraft }) {
  const eligibility = draft.eligibility_snapshot as {
    decision_type?: string;
    policy_id?: string | null;
    policy_version?: string | null;
  };
  return (
    <article className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold">{draft.business_name}</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            {[draft.sector, draft.area].filter(Boolean).join(" · ")}
          </p>
        </div>
        <Badge className="border-amber-300 bg-amber-50 text-amber-900">Not sent</Badge>
      </div>
      <p className="mt-4 whitespace-pre-wrap rounded-lg bg-muted/50 p-3 text-sm leading-relaxed">
        {draft.rendered_body}
      </p>
      <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
        <span>{draft.sms_encoding?.toUpperCase() ?? "Email"}</span>
        <span>·</span>
        <span>
          {draft.sms_characters ?? draft.sms_units ?? 0}{" "}
          {(draft.sms_characters ?? draft.sms_units ?? 0) === 1
            ? "character"
            : "characters"}
        </span>
        <span>·</span>
        <span>{draft.sms_segments ?? "—"} segment{draft.sms_segments === 1 ? "" : "s"}</span>
      </div>
      {(draft.sms_segments ?? 0) > 1 && (
        <p className="mt-2 text-xs font-medium text-amber-800">
          This message needs {draft.sms_segments} SMS segments, so delivery may cost more.
        </p>
      )}
      <p className="mt-2 text-xs text-muted-foreground">
        Research:{" "}
        {draft.research_date
          ? `checked ${new Date(`${draft.research_date}T00:00:00Z`).toLocaleDateString()}`
          : "date not recorded"}
      </p>
      {draft.research_stale && (
        <p className="mt-2 text-xs font-medium text-amber-800">
          Research is missing or over 90 days old. Re-check the website claim before approval.
        </p>
      )}
      <details className="mt-3 text-xs">
        <summary className="cursor-pointer text-muted-foreground">Eligibility snapshot</summary>
        <p className="mt-2 break-all font-mono text-muted-foreground">
          {eligibility.decision_type ?? "none"} · {eligibility.policy_id ?? "no policy"} ·{" "}
          {eligibility.policy_version ?? "—"}
        </p>
        <p className="mt-1 text-muted-foreground">
          {draft.sms_units ?? 0} encoded units · input fingerprint{" "}
          {String(draft.eligibility_snapshot.input_fingerprint ?? "not recorded")}
        </p>
      </details>
    </article>
  );
}

function CampaignStatus({ status }: { status: CampaignDetailRecord["status"] }) {
  return <Badge variant="outline" className="capitalize">{status}</Badge>;
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-muted-foreground">{label}</dt>
      <dd className="mt-1 font-medium">{value}</dd>
    </div>
  );
}

function groupSkips(rows: CampaignSkip[]): Record<string, CampaignSkip[]> {
  return rows.reduce<Record<string, CampaignSkip[]>>((groups, row) => {
    (groups[row.label] ??= []).push(row);
    return groups;
  }, {});
}
