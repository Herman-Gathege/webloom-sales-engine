import { Pencil, Plus, Power } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import {
  containsRawContact,
  createTemplate,
  listOffers,
  listTemplates,
  updateTemplate,
  variablesInBody,
  type MessageTemplate,
  type Offer,
  type TemplateChannel,
  type TemplateInput,
} from "@/api/catalog";
import { useAuth } from "@/auth/context";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

const ALLOWED_VARIABLES = [
  "business_name",
  "sector",
  "area",
  "website_status",
  "has_website",
  "offer_name",
  "price_range",
  "pitch_angle",
  "opt_out",
];

interface TemplateFormState {
  offer_id: string;
  channel: TemplateChannel;
  name: string;
  variant: string;
  body: string;
  is_active: boolean;
}

const EMPTY_FORM: TemplateFormState = {
  offer_id: "",
  channel: "sms",
  name: "",
  variant: "A",
  body: "Hi {{business_name}},\n\n{{opt_out}}",
  is_active: true,
};

export function TemplateCatalog() {
  const { user } = useAuth();
  const canManage = user?.role === "admin";
  const [offers, setOffers] = useState<Offer[]>([]);
  const [templates, setTemplates] = useState<MessageTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<TemplateFormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [filterOffer, setFilterOffer] = useState("");
  const [filterChannel, setFilterChannel] = useState<"" | TemplateChannel>("");

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      listOffers(canManage),
      listTemplates({ includeInactive: canManage }),
    ])
      .then(([offerRows, templateRows]) => {
        if (!cancelled) {
          setOffers(offerRows);
          setTemplates(templateRows);
          setError(null);
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "Could not load templates.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [canManage]);

  function closeForm() {
    setFormOpen(false);
    setEditingId(null);
    setForm({ ...EMPTY_FORM, offer_id: offers[0]?.id ?? "" });
    setError(null);
  }

  function openNewForm() {
    setEditingId(null);
    setForm({ ...EMPTY_FORM, offer_id: offers[0]?.id ?? "" });
    setError(null);
    setFormOpen(true);
  }

  function editTemplate(template: MessageTemplate) {
    setError(null);
    setEditingId(template.id);
    setForm({
      offer_id: template.offer_id,
      channel: template.channel,
      name: template.name,
      variant: template.variant,
      body: template.body,
      is_active: template.is_active,
    });
    setFormOpen(true);
  }

  async function saveTemplate(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const variables = variablesInBody(form.body);
    const unknown = variables.filter((value) => !ALLOWED_VARIABLES.includes(value));
    if (unknown.length > 0) {
      setError(`Unknown variables: ${unknown.join(", ")}.`);
      return;
    }
    if (form.is_active && !variables.includes("opt_out")) {
      setError("Active templates must include {{opt_out}}.");
      return;
    }
    if (containsRawContact(form.body)) {
      setError("Templates cannot contain raw contact details; use lead variables instead.");
      return;
    }
    if (!form.offer_id) {
      setError("Choose an offer.");
      return;
    }
    const payload: TemplateInput = {
      offer_id: form.offer_id,
      channel: form.channel,
      name: form.name.trim(),
      variant: form.variant.trim().toUpperCase(),
      body: form.body.trim(),
      variables,
      is_active: form.is_active,
    };
    setSaving(true);
    try {
      if (editingId) await updateTemplate(editingId, payload);
      else await createTemplate(payload);
      closeForm();
      const [offerRows, templateRows] = await Promise.all([
        listOffers(canManage),
        listTemplates({ includeInactive: canManage }),
      ]);
      setOffers(offerRows);
      setTemplates(templateRows);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not save the template.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleTemplate(template: MessageTemplate) {
    setError(null);
    try {
      await updateTemplate(template.id, { is_active: !template.is_active });
      setTemplates(await listTemplates({ includeInactive: canManage }));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not update the template.");
    }
  }

  const offerNames = new Map(offers.map((offer) => [offer.id, offer.name]));
  const visibleTemplates = templates.filter(
    (template) =>
      (!filterOffer || template.offer_id === filterOffer) &&
      (!filterChannel || template.channel === filterChannel),
  );

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader className="flex-row items-start justify-between gap-4">
          <div>
            <CardTitle>Templates</CardTitle>
            <CardDescription>
              Reusable email and SMS copy for each offer.
            </CardDescription>
          </div>
          {canManage && (
            <Button size="sm" onClick={openNewForm}>
              <Plus className="size-4" />
              New template
            </Button>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          {error && !formOpen && (
            <p role="alert" className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </p>
          )}

          <Dialog
            open={formOpen && canManage}
            onOpenChange={(open) => {
              if (!open) closeForm();
            }}
          >
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{editingId ? "Edit template" : "New template"}</DialogTitle>
                <DialogDescription>
                  Prepare reusable copy and validate its personalisation variables.
                </DialogDescription>
              </DialogHeader>
              {error && (
                <p role="alert" className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  {error}
                </p>
              )}
              <form onSubmit={saveTemplate} className="grid gap-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="space-y-1.5 text-sm">
                    <span className="font-medium">Offer</span>
                    <select
                      required
                      aria-label="Template offer"
                      className="h-10 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                      value={form.offer_id}
                      onChange={(event) => setForm({ ...form, offer_id: event.target.value })}
                    >
                      {offers.map((offer) => (
                        <option key={offer.id} value={offer.id}>
                          {offer.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="space-y-1.5 text-sm">
                    <span className="font-medium">Channel</span>
                    <select
                      aria-label="Template channel"
                      className="h-10 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                      value={form.channel}
                      onChange={(event) =>
                        setForm({
                          ...form,
                          channel: event.target.value as TemplateChannel,
                        })
                      }
                    >
                      <option value="sms">SMS</option>
                      <option value="email">Email</option>
                    </select>
                  </label>
                  <label className="space-y-1.5 text-sm">
                    <span className="font-medium">Name</span>
                    <Input
                      required
                      value={form.name}
                      onChange={(event) => setForm({ ...form, name: event.target.value })}
                    />
                  </label>
                  <label className="space-y-1.5 text-sm">
                    <span className="font-medium">Variant</span>
                    <Input
                      required
                      maxLength={16}
                      value={form.variant}
                      onChange={(event) => setForm({ ...form, variant: event.target.value })}
                    />
                  </label>
                  <label className="space-y-1.5 text-sm sm:col-span-2">
                    <span className="font-medium">Body</span>
                    <textarea
                      required
                      aria-label="Template body"
                      className="min-h-44 w-full rounded-md border border-input bg-transparent px-3 py-2 font-mono text-sm leading-relaxed"
                      value={form.body}
                      onChange={(event) => setForm({ ...form, body: event.target.value })}
                    />
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={form.is_active}
                      onChange={(event) =>
                        setForm({ ...form, is_active: event.target.checked })
                      }
                    />
                    Active
                  </label>
                </div>
                <div className="rounded-lg border border-border bg-background p-3 text-xs">
                  <p className="font-medium">Variables detected</p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {variablesInBody(form.body).map((variable) => (
                      <Badge key={variable} variant="outline" className="font-mono font-normal">
                        {variable}
                      </Badge>
                    ))}
                  </div>
                  <p className="mt-3 leading-relaxed text-muted-foreground">
                    Allowed: {ALLOWED_VARIABLES.join(", ")}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button type="submit" disabled={saving}>
                    {saving ? "Saving…" : editingId ? "Save changes" : "Create template"}
                  </Button>
                  <Button type="button" variant="outline" onClick={closeForm}>
                    Cancel
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>

          <div className="grid gap-2 sm:grid-cols-2">
            <label className="space-y-1 text-sm">
              <span className="text-xs font-medium text-muted-foreground">Filter by offer</span>
              <select
                aria-label="Filter templates by offer"
                className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                value={filterOffer}
                onChange={(event) => setFilterOffer(event.target.value)}
              >
                <option value="">All offers</option>
                {offers.map((offer) => (
                  <option key={offer.id} value={offer.id}>
                    {offer.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-sm">
              <span className="text-xs font-medium text-muted-foreground">Filter by channel</span>
              <select
                aria-label="Filter templates by channel"
                className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                value={filterChannel}
                onChange={(event) =>
                  setFilterChannel(event.target.value as "" | TemplateChannel)
                }
              >
                <option value="">All channels</option>
                <option value="sms">SMS</option>
                <option value="email">Email</option>
              </select>
            </label>
          </div>

          {loading ? (
            <p className="text-sm text-muted-foreground">Loading templates…</p>
          ) : visibleTemplates.length === 0 ? (
            <p className="rounded-xl border border-dashed p-6 text-sm text-muted-foreground">
              No templates match these filters.
            </p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {visibleTemplates.map((template) => (
                <article key={template.id} className="rounded-xl border border-border bg-card p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h2 className="font-semibold">{template.name}</h2>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {offerNames.get(template.offer_id) ?? "Unknown offer"} ·{" "}
                        {template.channel.toUpperCase()} · Variant {template.variant}
                      </p>
                    </div>
                    <Badge variant={template.is_active ? "secondary" : "outline"}>
                      {template.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                  <pre className="mt-3 whitespace-pre-wrap rounded-lg bg-muted/60 p-3 font-sans text-sm leading-relaxed">
                    {template.body}
                  </pre>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {template.variables.map((variable) => (
                      <Badge key={variable} variant="outline" className="font-mono font-normal">
                        {variable}
                      </Badge>
                    ))}
                  </div>
                  {canManage && (
                    <div className="mt-4 flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => editTemplate(template)}
                      >
                        <Pencil className="size-4" />
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => void toggleTemplate(template)}
                      >
                        <Power className="size-4" />
                        {template.is_active ? "Deactivate" : "Reactivate"}
                      </Button>
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
