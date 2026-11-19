import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  createCampaign,
  getCampaign,
  previewCampaign,
  updateCampaign,
  type CampaignInput,
  type CampaignPreview,
  type CampaignSelectionContext,
} from "@/api/campaign";
import { listOffers, listTemplates, type MessageTemplate, type Offer } from "@/api/catalog";
import { getLeadFilterOptions, listLeads } from "@/api/leads";
import type {
  ComplianceStatus,
  DataQualityStatus,
  Lead,
  LeadFilterOptions,
  LeadListParams,
  LeadStatus,
} from "@/api/types";
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

const PAGE_SIZE = 25;

interface FormState {
  name: string;
  goal: string;
  offer_id: string;
  template_id: string;
}

const EMPTY_FORM: FormState = {
  name: "",
  goal: "",
  offer_id: "",
  template_id: "",
};

export function CampaignCreate() {
  const { id } = useParams<{ id: string }>();
  const editing = Boolean(id);
  const navigate = useNavigate();
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [templates, setTemplates] = useState<MessageTemplate[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [selectionContext, setSelectionContext] =
    useState<CampaignSelectionContext>({});
  const [selectionContextReady, setSelectionContextReady] = useState(!editing);
  const [preview, setPreview] = useState<CampaignPreview | null>(null);
  const [saving, setSaving] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([listOffers(false), listTemplates({ includeInactive: false })])
      .then(([offerRows, templateRows]) => {
        if (cancelled) return;
        setOffers(offerRows);
        setTemplates(templateRows.filter((row) => row.channel === "sms"));
        if (!editing) {
          const firstTemplate = templateRows.find((row) => row.channel === "sms");
          const firstOfferId = firstTemplate?.offer_id ?? offerRows[0]?.id ?? "";
          setForm((current) => ({
            ...current,
            offer_id: current.offer_id || firstOfferId,
            template_id: current.template_id || firstTemplate?.id || "",
          }));
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "Could not load the catalogue.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [editing]);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    getCampaign(id)
      .then((campaign) => {
        if (cancelled) return;
        if (campaign.status !== "draft") {
          setError("Only ungenerated, unarchived campaigns can be edited.");
          setSelectionContextReady(true);
          return;
        }
        setForm({
          name: campaign.name,
          goal: campaign.goal,
          offer_id: campaign.offer_id,
          template_id: campaign.template_id,
        });
        setSelectionContext(campaign.selection_context);
        setSelectedIds(campaign.selected_lead_ids);
        setSelectionContextReady(true);
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "Could not load the campaign.");
          setSelectionContextReady(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const selectedTemplates = templates.filter(
    (template) => template.offer_id === form.offer_id,
  );

  function updateForm(changes: Partial<FormState>) {
    setForm((current) => ({ ...current, ...changes }));
    setPreview(null);
  }

  function toggleLead(leadId: string) {
    setPreview(null);
    setSelectedIds((current) => {
      if (current.includes(leadId)) return current.filter((value) => value !== leadId);
      if (current.length >= 200) return current;
      return [...current, leadId];
    });
  }

  function campaignInput(): CampaignInput {
    return {
      ...form,
      channel: "sms",
      lead_ids: selectedIds,
      selection_context: selectionContext,
    };
  }

  const updateSelectionContext = useCallback(
    (context: CampaignSelectionContext) => {
      setSelectionContext(context);
      setPreview(null);
    },
    [],
  );

  async function runPreview() {
    setError(null);
    if (!form.name.trim() || !form.goal.trim()) {
      setError("Enter a campaign name and goal.");
      return;
    }
    if (!form.offer_id || !form.template_id) {
      setError("Choose an active offer and SMS template.");
      return;
    }
    if (selectedIds.length === 0) {
      setError("Select at least one lead.");
      return;
    }
    setPreviewing(true);
    try {
      setPreview(await previewCampaign(campaignInput()));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not preview the campaign.");
    } finally {
      setPreviewing(false);
    }
  }

  async function save() {
    if (!preview) {
      setError("Preview the campaign before saving it.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const result = editing && id
        ? await updateCampaign(id, campaignInput())
        : await createCampaign(campaignInput());
      navigate(`/campaigns/${result.id}`, { replace: true });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not save the campaign.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-5">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link to="/campaigns">← Back to campaigns</Link>
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>{editing ? "Edit campaign" : "New campaign"}</CardTitle>
          <CardDescription>
            Sprint 5 prepares SMS drafts only. Nothing is approved or sent here.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          {error && <p role="alert" className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</p>}
          <div className="grid gap-3 md:grid-cols-2">
            <label className="space-y-1.5 text-sm">
              <span className="font-medium">Campaign name</span>
              <Input
                value={form.name}
                onChange={(event) => updateForm({ name: event.target.value })}
                placeholder="Westlands no-website outreach"
              />
            </label>
            <label className="space-y-1.5 text-sm">
              <span className="font-medium">Goal</span>
              <Input
                value={form.goal}
                onChange={(event) => updateForm({ goal: event.target.value })}
                placeholder="Book five discovery calls this month"
              />
              <span className="block text-xs font-normal text-muted-foreground">
                Describe the business outcome, not the message body.
              </span>
            </label>
            <label className="space-y-1.5 text-sm">
              <span className="font-medium">Offer</span>
              <select
                aria-label="Campaign offer"
                className="h-10 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                value={form.offer_id}
                onChange={(event) => {
                  const offerId = event.target.value;
                  const firstTemplate = templates.find(
                    (row) => row.offer_id === offerId,
                  );
                  updateForm({
                    offer_id: offerId,
                    template_id: firstTemplate?.id || "",
                  });
                }}
              >
                {offers.map((offer) => (
                  <option key={offer.id} value={offer.id}>{offer.name}</option>
                ))}
              </select>
            </label>
            <label className="space-y-1.5 text-sm">
              <span className="font-medium">SMS template</span>
              <select
                aria-label="Campaign SMS template"
                className="h-10 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                value={form.template_id}
                onChange={(event) => updateForm({ template_id: event.target.value })}
              >
                <option value="">Choose a template</option>
                {selectedTemplates.map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.name} · {template.variant}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </CardContent>
      </Card>

      {selectionContextReady ? (
        <LeadSelector
          selectedIds={selectedIds}
          onToggle={toggleLead}
          onClear={() => {
            setSelectedIds([]);
            setPreview(null);
          }}
          onFiltersChange={updateSelectionContext}
          initialContext={selectionContext}
        />
      ) : (
        <p className="text-sm text-muted-foreground">Loading campaign selection…</p>
      )}

      {preview && (
        <PreviewSummary preview={preview} />
      )}

      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-3 pt-5">
          <p className="text-sm text-muted-foreground">
            {selectedIds.length} of 200 leads selected
          </p>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" onClick={() => void runPreview()} disabled={previewing}>
              {previewing ? "Checking…" : "Preview campaign"}
            </Button>
            <Button type="button" onClick={() => void save()} disabled={!preview || saving}>
              {saving ? "Saving…" : editing ? "Save changes" : "Create campaign"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function LeadSelector({
  selectedIds,
  onToggle,
  onClear,
  onFiltersChange,
  initialContext,
}: {
  selectedIds: string[];
  onToggle: (leadId: string) => void;
  onClear: () => void;
  onFiltersChange: (context: CampaignSelectionContext) => void;
  initialContext: CampaignSelectionContext;
}) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [options, setOptions] = useState<LeadFilterOptions | null>(null);
  const [q, setQ] = useState(initialContext.q ?? "");
  const [sector, setSector] = useState(initialContext.sector ?? "");
  const [area, setArea] = useState(initialContext.area ?? "");
  const [source, setSource] = useState(initialContext.source ?? "");
  const [website, setWebsite] = useState(initialContext.website ?? "");
  const [complianceStatus, setComplianceStatus] = useState(
    initialContext.compliance_status ?? "",
  );
  const [dataQuality, setDataQuality] = useState(
    initialContext.data_quality_status ?? "",
  );
  const [provenance, setProvenance] = useState(initialContext.provenance ?? "");
  const [outreachReady, setOutreachReady] = useState(
    initialContext.outreach_ready === undefined
      ? ""
      : initialContext.outreach_ready
        ? "yes"
        : "no",
  );
  const [exceptionReview, setExceptionReview] = useState(
    initialContext.exception_review === undefined
      ? ""
      : initialContext.exception_review
        ? "true"
        : "false",
  );
  const [hasSuppression, setHasSuppression] = useState(
    initialContext.has_suppression === undefined
      ? ""
      : initialContext.has_suppression
        ? "yes"
        : "no",
  );
  const [batchId, setBatchId] = useState(initialContext.batch_id ?? "");
  const [status, setStatus] = useState(initialContext.status ?? "");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getLeadFilterOptions().then((loaded) => setOptions(loaded.data)).catch(() => undefined);
  }, []);

  useEffect(() => {
    onFiltersChange({
      ...(q ? { q } : {}),
      ...(sector ? { sector } : {}),
      ...(area ? { area } : {}),
      ...(source ? { source } : {}),
      ...(website
        ? { website: website as CampaignSelectionContext["website"] }
        : {}),
      ...(status ? { status } : {}),
      ...(complianceStatus
        ? {
            compliance_status:
              complianceStatus as CampaignSelectionContext["compliance_status"],
          }
        : {}),
      ...(dataQuality
        ? {
            data_quality_status:
              dataQuality as CampaignSelectionContext["data_quality_status"],
          }
        : {}),
      ...(provenance
        ? { provenance: provenance as CampaignSelectionContext["provenance"] }
        : {}),
      ...(outreachReady
        ? { outreach_ready: outreachReady === "yes" }
        : {}),
      ...(exceptionReview
        ? { exception_review: exceptionReview === "true" }
        : {}),
      ...(hasSuppression
        ? { has_suppression: hasSuppression === "yes" }
        : {}),
      ...(batchId ? { batch_id: batchId } : {}),
    });
  }, [
    area,
    batchId,
    complianceStatus,
    dataQuality,
    exceptionReview,
    hasSuppression,
    onFiltersChange,
    outreachReady,
    provenance,
    q,
    sector,
    source,
    status,
    website,
  ]);

  useEffect(() => {
    let cancelled = false;
    const params: LeadListParams = {
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
      q: q || undefined,
      sector: sector || undefined,
      area: area || undefined,
      source: source || undefined,
      website: (website || undefined) as "yes" | "no" | "unknown" | undefined,
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
      sort: "newest",
    };
    listLeads(params)
      .then((loaded) => {
        if (cancelled) return;
        setLeads(loaded.data.items);
        setTotal(loaded.data.total);
        setError(null);
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "Could not load leads.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
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
    q,
    sector,
    source,
    status,
    website,
  ]);

  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-3">
        <div>
          <CardTitle>Select leads</CardTitle>
          <CardDescription>Filters narrow the list; each campaign stores explicit selections.</CardDescription>
        </div>
        <Badge variant="secondary">{selectedIds.length} selected</Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid min-w-0 grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
          <Input
            type="search"
            aria-label="Search campaign leads"
            placeholder="Search business, phone, area"
            className="min-w-0"
            value={q}
            onChange={(event) => {
              setQ(event.target.value);
              setPage(1);
            }}
          />
          <select
            aria-label="Campaign sector filter"
            className="h-10 w-full min-w-0 rounded-md border border-input bg-transparent px-3 text-sm"
            value={sector}
            onChange={(event) => {
              setSector(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All sectors</option>
            {(options?.sectors ?? []).map((value) => (
              <option key={value} value={value}>{value}</option>
            ))}
          </select>
          <select
            aria-label="Campaign area filter"
            className="h-10 w-full min-w-0 rounded-md border border-input bg-transparent px-3 text-sm"
            value={area}
            onChange={(event) => {
              setArea(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All areas</option>
            {(options?.areas ?? []).map((value) => (
              <option key={value} value={value}>{value}</option>
            ))}
          </select>
          <select
            aria-label="Campaign website filter"
            className="h-10 w-full min-w-0 rounded-md border border-input bg-transparent px-3 text-sm"
            value={website}
            onChange={(event) => {
              setWebsite(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Any website state</option>
            <option value="no">No website</option>
            <option value="yes">Has website</option>
            <option value="unknown">Unknown / not checked</option>
          </select>
          <select
            aria-label="Campaign source filter"
            className="h-10 w-full min-w-0 rounded-md border border-input bg-transparent px-3 text-sm"
            value={source}
            onChange={(event) => {
              setSource(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Any source</option>
            {(options?.sources ?? []).map((value) => (
              <option key={value} value={value}>{value}</option>
            ))}
          </select>
          <select
            aria-label="Campaign status filter"
            className="h-10 w-full min-w-0 rounded-md border border-input bg-transparent px-3 text-sm"
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Any status</option>
            {(options?.statuses ?? []).map((value) => (
              <option key={value} value={value}>{value.replaceAll("_", " ")}</option>
            ))}
          </select>
          <select
            aria-label="Campaign compliance filter"
            className="h-10 w-full min-w-0 rounded-md border border-input bg-transparent px-3 text-sm"
            value={complianceStatus}
            onChange={(event) => {
              setComplianceStatus(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Any compliance state</option>
            <option value="eligible">Eligible</option>
            <option value="needs_review">Needs review</option>
            <option value="blocked">Blocked</option>
            <option value="invalid">Invalid</option>
          </select>
          <select
            aria-label="Campaign data quality filter"
            className="h-10 w-full min-w-0 rounded-md border border-input bg-transparent px-3 text-sm"
            value={dataQuality}
            onChange={(event) => {
              setDataQuality(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Any data quality</option>
            {(options?.data_quality_statuses ?? []).map((value) => (
              <option key={value} value={value}>{value.replaceAll("_", " ")}</option>
            ))}
          </select>
          <select
            aria-label="Campaign provenance filter"
            className="h-10 w-full min-w-0 rounded-md border border-input bg-transparent px-3 text-sm"
            value={provenance}
            onChange={(event) => {
              setProvenance(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Any provenance</option>
            <option value="available">Source available</option>
            <option value="missing">Source missing</option>
            <option value="incomplete">Source incomplete</option>
          </select>
          <select
            aria-label="Campaign outreach readiness filter"
            className="h-10 w-full min-w-0 rounded-md border border-input bg-transparent px-3 text-sm"
            value={outreachReady}
            onChange={(event) => {
              setOutreachReady(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Any readiness</option>
            <option value="yes">Ready</option>
            <option value="no">Not ready</option>
          </select>
          <select
            aria-label="Campaign exception review filter"
            className="h-10 w-full min-w-0 rounded-md border border-input bg-transparent px-3 text-sm"
            value={exceptionReview}
            onChange={(event) => {
              setExceptionReview(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Any exception state</option>
            <option value="true">Needs exception review</option>
            <option value="false">No exception review</option>
          </select>
          <select
            aria-label="Campaign suppression filter"
            className="h-10 w-full min-w-0 rounded-md border border-input bg-transparent px-3 text-sm"
            value={hasSuppression}
            onChange={(event) => {
              setHasSuppression(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Any restriction state</option>
            <option value="yes">Has restriction</option>
            <option value="no">No restriction</option>
          </select>
          <select
            aria-label="Campaign import batch filter"
            className="h-10 w-full min-w-0 rounded-md border border-input bg-transparent px-3 text-sm"
            value={batchId}
            onChange={(event) => {
              setBatchId(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Any import batch</option>
            {(options?.import_batches ?? []).map((batch) => (
              <option key={batch.id} value={batch.id}>{batch.filename}</option>
            ))}
          </select>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs text-muted-foreground">{total} matching leads</p>
          {selectedIds.length > 0 && (
            <Button type="button" variant="link" size="sm" className="h-auto p-0" onClick={onClear}>
              Clear selections
            </Button>
          )}
        </div>
        {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
        {loading ? (
          <p className="text-sm text-muted-foreground">Loading leads…</p>
        ) : leads.length === 0 ? (
          <p className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
            No leads match these filters.
          </p>
        ) : (
          <div className="space-y-2">
            {leads.map((lead) => {
              const selected = selectedIds.includes(lead.id);
              return (
                <label
                  key={lead.id}
                  className="flex cursor-pointer items-start gap-3 rounded-xl border border-border bg-card p-3 hover:bg-accent"
                >
                  <input
                    type="checkbox"
                    className="mt-1"
                    checked={selected}
                    disabled={!selected && selectedIds.length >= 200}
                    onChange={() => onToggle(lead.id)}
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block font-medium">{lead.business_name}</span>
                    <span className="mt-1 block text-xs text-muted-foreground">
                      {[lead.sector, lead.area, lead.phone].filter(Boolean).join(" · ")}
                    </span>
                    <span className="mt-2 flex flex-wrap gap-2">
                      <ComplianceStatusBadge status={lead.compliance.status} />
                      <Badge variant="outline">
                        {lead.website_presence === "has_website"
                          ? "Has website"
                          : lead.website_presence === "no_website"
                            ? "No website"
                            : "Website unknown"}
                      </Badge>
                    </span>
                  </span>
                </label>
              );
            })}
          </div>
        )}
        {pageCount > 1 && (
          <div className="flex items-center justify-between border-t border-border pt-3">
            <Button type="button" variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
              Previous
            </Button>
            <span className="text-xs text-muted-foreground">Page {page} of {pageCount}</span>
            <Button type="button" variant="outline" size="sm" disabled={page >= pageCount} onClick={() => setPage((value) => value + 1)}>
              Next
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PreviewSummary({ preview }: { preview: CampaignPreview }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Preview</CardTitle>
        <CardDescription>
          {preview.eligible_count} eligible · {preview.skipped_count} skipped
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {Object.keys(preview.reason_counts).length > 0 && (
          <div>
            <p className="text-sm font-medium">Skip reasons</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {Object.entries(preview.reason_counts).map(([label, count]) => (
                <Badge key={label} variant="outline">{label}: {count}</Badge>
              ))}
            </div>
          </div>
        )}
        <div className="grid gap-2 md:grid-cols-2">
          {preview.eligible.map((lead) => (
            <div key={lead.lead_id} className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">
              <p className="font-medium">{lead.business_name}</p>
              <p className="mt-1 text-xs text-emerald-900">
                {lead.decision_type === "automated_policy" ? "Policy eligible" : "Human review eligible"}
              </p>
              {lead.research_stale && (
                <p className="mt-2 text-xs font-medium text-amber-800">
                  Research date is missing or over 90 days old. Re-check before using website claims.
                </p>
              )}
            </div>
          ))}
          {preview.skipped.map((lead) => (
            <div key={lead.lead_id} className="rounded-lg border border-amber-200 bg-amber-50 p-3">
              <p className="font-medium">{lead.business_name}</p>
              <p className="mt-1 text-xs text-amber-900">{lead.label} · {lead.explanation}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
