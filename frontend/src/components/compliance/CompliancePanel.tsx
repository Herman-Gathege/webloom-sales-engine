import { useState } from "react";

import { recordSuppression, reviewEligibility } from "@/api/leads";
import type {
  Channel,
  ChannelEligibility,
  EligibilityReviewInput,
  EligibilityState,
  LawfulBasis,
  LeadDetail,
  SuppressionReason,
  SuppressionScope,
} from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const textareaClass =
  "min-h-20 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50";

function labelClass() {
  return "text-xs font-medium tracking-wide text-muted-foreground uppercase";
}

function stateClass(state: ChannelEligibility["effective_state"]): string {
  if (state === "eligible") return "border-emerald-300 bg-emerald-50 text-emerald-800";
  if (state === "suppressed") return "border-red-300 bg-red-50 text-red-800";
  return "border-amber-300 bg-amber-50 text-amber-800";
}

function label(value: string): string {
  return value.replaceAll("_", " ");
}

function ChannelReviewForm({
  leadId,
  record,
  sampleMode,
  onUpdated,
}: {
  leadId: string;
  record: ChannelEligibility;
  sampleMode: boolean;
  onUpdated: (lead: LeadDetail) => void;
}) {
  const [state, setState] = useState<EligibilityState>(record.state);
  const [lawfulBasis, setLawfulBasis] = useState<LawfulBasis | "">(
    record.lawful_basis ?? "",
  );
  const [evidenceSummary, setEvidenceSummary] = useState(record.evidence_summary ?? "");
  const [evidenceSource, setEvidenceSource] = useState(record.evidence_source ?? "");
  const [purpose, setPurpose] = useState(record.intended_purpose ?? "");
  const [contactContext, setContactContext] = useState(record.contact_context ?? "");
  const [reviewer, setReviewer] = useState(record.reviewer ?? "");
  const [rationale, setRationale] = useState(record.rationale ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    setSaving(true);
    setError(null);
    const decision: EligibilityReviewInput = {
      state,
      lawful_basis: lawfulBasis || null,
      evidence_summary: evidenceSummary.trim() || null,
      evidence_source: evidenceSource.trim() || null,
      intended_purpose: purpose.trim() || null,
      contact_context: contactContext.trim() || null,
      reviewer: reviewer.trim(),
      rationale: rationale.trim(),
    };
    try {
      onUpdated(await reviewEligibility(leadId, record.channel, decision));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not save the review.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-3 rounded-lg border p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-medium uppercase">{record.channel}</p>
          <p className="text-xs text-muted-foreground">
            Reviewed {record.reviewed_at ? new Date(record.reviewed_at).toLocaleString() : "—"}
            {record.reviewer ? ` by ${record.reviewer}` : ""}
          </p>
        </div>
        <Badge variant="outline" className={stateClass(record.effective_state)}>
          {label(record.effective_state)}
        </Badge>
      </div>

      {record.effective_state === "suppressed" ? (
        <p className="text-sm text-red-800">
          Suppression is terminal. It overrides the saved review for this channel.
        </p>
      ) : (
        <details className="space-y-3">
          <summary className="cursor-pointer text-sm font-medium">
            Review {record.channel}
          </summary>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <label className="space-y-1">
              <span className={labelClass()}>Decision</span>
              <select
                aria-label={`${record.channel} decision`}
                className="h-9 w-full rounded-md border border-input bg-transparent px-2 text-sm disabled:opacity-50"
                disabled={sampleMode || saving}
                value={state}
                onChange={(event) => setState(event.target.value as EligibilityState)}
              >
                <option value="needs_review">needs review</option>
                <option value="eligible">eligible</option>
              </select>
            </label>
            <label className="space-y-1">
              <span className={labelClass()}>Lawful basis</span>
              <select
                aria-label={`${record.channel} lawful basis`}
                className="h-9 w-full rounded-md border border-input bg-transparent px-2 text-sm disabled:opacity-50"
                disabled={sampleMode || saving}
                value={lawfulBasis}
                onChange={(event) => setLawfulBasis(event.target.value as LawfulBasis | "")}
              >
                <option value="">Not assessed</option>
                <option value="consent">consent</option>
                <option value="contract">contract</option>
                <option value="legal_obligation">legal obligation</option>
                <option value="vital_interests">vital interests</option>
                <option value="public_task">public task</option>
                <option value="legitimate_interests">legitimate interests</option>
                <option value="other">other</option>
              </select>
            </label>
            <label className="space-y-1">
              <span className={labelClass()}>Reviewed by</span>
              <input
                aria-label={`${record.channel} reviewer`}
                className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm disabled:opacity-50"
                disabled={sampleMode || saving}
                value={reviewer}
                onChange={(event) => setReviewer(event.target.value)}
              />
            </label>
            <label className="space-y-1">
              <span className={labelClass()}>Intended purpose</span>
              <input
                aria-label={`${record.channel} intended purpose`}
                className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm disabled:opacity-50"
                disabled={sampleMode || saving}
                value={purpose}
                onChange={(event) => setPurpose(event.target.value)}
              />
            </label>
          </div>
          <label className="block space-y-1">
            <span className={labelClass()}>Decision rationale</span>
            <textarea
              aria-label={`${record.channel} rationale`}
              className={textareaClass}
              disabled={sampleMode || saving}
              value={rationale}
              onChange={(event) => setRationale(event.target.value)}
            />
          </label>
          <label className="block space-y-1">
            <span className={labelClass()}>Evidence summary</span>
            <textarea
              aria-label={`${record.channel} evidence summary`}
              className={textareaClass}
              disabled={sampleMode || saving}
              value={evidenceSummary}
              onChange={(event) => setEvidenceSummary(event.target.value)}
            />
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="space-y-1">
              <span className={labelClass()}>Evidence source</span>
              <input
                aria-label={`${record.channel} evidence source`}
                className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm disabled:opacity-50"
                disabled={sampleMode || saving}
                value={evidenceSource}
                onChange={(event) => setEvidenceSource(event.target.value)}
              />
            </label>
            <label className="space-y-1">
              <span className={labelClass()}>Contact context</span>
              <input
                aria-label={`${record.channel} contact context`}
                className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm disabled:opacity-50"
                disabled={sampleMode || saving}
                value={contactContext}
                onChange={(event) => setContactContext(event.target.value)}
              />
            </label>
          </div>
          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}
          <Button
            type="button"
            size="sm"
            disabled={
              sampleMode ||
              saving ||
              !reviewer.trim() ||
              !rationale.trim() ||
              (state === "eligible" &&
                (!lawfulBasis ||
                  !evidenceSummary.trim() ||
                  !evidenceSource.trim() ||
                  !purpose.trim() ||
                  !contactContext.trim()))
            }
            onClick={save}
          >
            {saving ? "Saving…" : `Save ${record.channel} review`}
          </Button>
        </details>
      )}
    </div>
  );
}

function SuppressionForm({
  lead,
  sampleMode,
  onUpdated,
}: {
  lead: LeadDetail;
  sampleMode: boolean;
  onUpdated: (lead: LeadDetail) => void;
}) {
  const [scope, setScope] = useState<SuppressionScope>("all_marketing");
  const [reason, setReason] = useState<SuppressionReason>("opt_out");
  const [source, setSource] = useState("");
  const [recordedBy, setRecordedBy] = useState("");
  const [note, setNote] = useState("");
  const [acknowledged, setAcknowledged] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    setSaving(true);
    setError(null);
    try {
      onUpdated(
        await recordSuppression(lead.id, {
          scope,
          reason,
          source: source.trim(),
          recorded_by: recordedBy.trim(),
          note: note.trim() || null,
        }),
      );
      setSource("");
      setRecordedBy("");
      setNote("");
      setAcknowledged(false);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not record the opt-out.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-3 rounded-lg border border-red-200 p-4">
      <div>
        <p className="font-medium">Record an objection or opt-out</p>
        <p className="text-xs text-muted-foreground">
          Restrictions are terminal and cannot be removed through this screen.
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="space-y-1">
          <span className={labelClass()}>Scope</span>
          <select
            aria-label="Suppression scope"
            className="h-9 w-full rounded-md border border-input bg-transparent px-2 text-sm disabled:opacity-50"
            disabled={sampleMode || saving}
            value={scope}
            onChange={(event) => {
              setScope(event.target.value as SuppressionScope);
              setAcknowledged(false);
            }}
          >
            <option value="all_marketing">all marketing</option>
            <option value="email">email only</option>
            <option value="sms">SMS only</option>
            <option value="whatsapp">WhatsApp only</option>
          </select>
        </label>
        <label className="space-y-1">
          <span className={labelClass()}>Reason</span>
          <select
            aria-label="Suppression reason"
            className="h-9 w-full rounded-md border border-input bg-transparent px-2 text-sm disabled:opacity-50"
            disabled={sampleMode || saving}
            value={reason}
            onChange={(event) => setReason(event.target.value as SuppressionReason)}
          >
            <option value="opt_out">opt out</option>
            <option value="objection">objection</option>
            <option value="manual_restriction">manual restriction</option>
          </select>
        </label>
        <label className="space-y-1">
          <span className={labelClass()}>Source</span>
          <input
            aria-label="Suppression source"
            className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm disabled:opacity-50"
            disabled={sampleMode || saving}
            value={source}
            onChange={(event) => setSource(event.target.value)}
          />
        </label>
        <label className="space-y-1">
          <span className={labelClass()}>Recorded by</span>
          <input
            aria-label="Suppression recorder"
            className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm disabled:opacity-50"
            disabled={sampleMode || saving}
            value={recordedBy}
            onChange={(event) => setRecordedBy(event.target.value)}
          />
        </label>
      </div>
      <label className="block space-y-1">
        <span className={labelClass()}>Short note</span>
        <textarea
          aria-label="Suppression note"
          className={textareaClass}
          disabled={sampleMode || saving}
          value={note}
          onChange={(event) => setNote(event.target.value)}
        />
      </label>
      {scope === "all_marketing" && (
        <label className="flex items-start gap-2 text-sm">
          <input
            type="checkbox"
            aria-label="Confirm all-marketing suppression"
            checked={acknowledged}
            disabled={sampleMode || saving}
            onChange={(event) => setAcknowledged(event.target.checked)}
          />
          I understand this suppresses every available marketing channel and is
          terminal.
        </label>
      )}
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}
      <Button
        type="button"
        variant="destructive"
        size="sm"
        disabled={
          sampleMode ||
          saving ||
          !source.trim() ||
          !recordedBy.trim() ||
          (scope === "all_marketing" && !acknowledged)
        }
        onClick={save}
      >
        {saving ? "Recording…" : "Record restriction"}
      </Button>
    </div>
  );
}

export function CompliancePanel({
  lead,
  sampleMode,
  onUpdated,
}: {
  lead: LeadDetail;
  sampleMode: boolean;
  onUpdated: (lead: LeadDetail) => void;
}) {
  const landline = Boolean(lead.phone) && /^\+254[2-6]/.test(lead.phone ?? "");
  const availability: Record<Channel, string> = {
    email: lead.email ? "technical contact available" : "no email recorded",
    sms: !lead.phone
      ? "no phone recorded"
      : landline
        ? "landline cannot receive SMS"
        : "technical contact available",
    whatsapp:
      lead.phone && lead.whatsapp_capable
        ? "technical contact available; delivery not implemented"
        : "not technically available",
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Compliance review</CardTitle>
        <CardDescription>
          Provenance and decisions are separate. A public contact is never approved
          automatically.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {sampleMode && (
          <p className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
            Review controls are disabled while the app is showing sample data. Reconnect
            the API before recording a real decision.
          </p>
        )}

        <div>
          <h3 className="mb-3 text-sm font-medium">Provenance</h3>
          {lead.provenance ? (
            <dl className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <dt className={labelClass()}>Collection</dt>
                <dd>{lead.provenance.collection_method ?? "Unknown"}</dd>
              </div>
              <div>
                <dt className={labelClass()}>Collected</dt>
                <dd>{lead.provenance.collection_date ?? "Unknown"}</dd>
              </div>
              <div>
                <dt className={labelClass()}>Contact type</dt>
                <dd>{label(lead.provenance.contact_type)}</dd>
              </div>
              <div>
                <dt className={labelClass()}>Intended purpose</dt>
                <dd>{lead.provenance.intended_purpose ?? "Not recorded"}</dd>
              </div>
              <div>
                <dt className={labelClass()}>Source URL</dt>
                <dd className="break-all">
                  {lead.provenance.source_url ?? "Not recorded"}
                </dd>
              </div>
              <div>
                <dt className={labelClass()}>Named contact</dt>
                <dd>{lead.provenance.contact_name ?? "—"}</dd>
              </div>
              <div>
                <dt className={labelClass()}>Import row</dt>
                <dd>{lead.provenance.row_number ?? "Unknown"}</dd>
              </div>
              <div>
                <dt className={labelClass()}>Import batch</dt>
                <dd className="font-mono text-xs break-all">
                  {lead.provenance.import_batch_id ?? "Unknown"}
                </dd>
              </div>
            </dl>
          ) : (
            <p className="text-sm text-amber-800">
              No provenance record yet. Keep this lead in review.
            </p>
          )}
        </div>

        <div className="space-y-3">
          <h3 className="text-sm font-medium">Channel eligibility</h3>
          {lead.eligibility.map((record) => (
            <div key={record.channel} className="space-y-1">
              <p className="text-xs text-muted-foreground">
                {record.channel}: {availability[record.channel]}
              </p>
              <ChannelReviewForm
                key={`${record.channel}-${record.reviewer}-${record.state}`}
                leadId={lead.id}
                record={record}
                sampleMode={sampleMode}
                onUpdated={onUpdated}
              />
            </div>
          ))}
        </div>

        {lead.suppressions.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium">Suppression history</h3>
            <ul className="space-y-2 text-sm">
              {lead.suppressions.map((entry) => (
                <li key={entry.id} className="rounded-md border p-3">
                  <p className="font-medium">
                    {label(entry.scope)} · {label(entry.reason)} · {entry.contact_kind}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {entry.source} · {entry.recorded_by} ·{" "}
                    {new Date(entry.created_at).toLocaleString()}
                  </p>
                  {entry.note && <p className="mt-1">{entry.note}</p>}
                </li>
              ))}
            </ul>
          </div>
        )}

        <SuppressionForm lead={lead} sampleMode={sampleMode} onUpdated={onUpdated} />
      </CardContent>
    </Card>
  );
}
