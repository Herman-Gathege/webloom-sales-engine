import { Plus } from "lucide-react";
import { useState, type FormEvent } from "react";

import { createLead } from "@/api/leads";
import type { LeadCreateInput, LeadDetail } from "@/api/types";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

interface AddLeadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: (lead: LeadDetail) => void;
}

interface FormState {
  business_name: string;
  phone: string;
  email: string;
  sector: string;
  area: string;
  website_status: string;
  source: string;
  source_url: string;
  has_website: boolean;
  whatsapp_capable: boolean;
}

const EMPTY_FORM: FormState = {
  business_name: "",
  phone: "",
  email: "",
  sector: "",
  area: "",
  website_status: "",
  source: "Manual entry",
  source_url: "",
  has_website: false,
  whatsapp_capable: true,
};

function optional(value: string): string | null {
  return value.trim() || null;
}

function payloadFor(form: FormState): LeadCreateInput {
  return {
    business_name: form.business_name.trim(),
    sector: optional(form.sector),
    area: optional(form.area),
    phone: optional(form.phone),
    email: optional(form.email),
    whatsapp_capable: form.whatsapp_capable,
    website_status: optional(form.website_status),
    has_website: form.has_website,
    source: form.source.trim(),
    source_url: optional(form.source_url),
  };
}

export function AddLeadDialog({ open, onOpenChange, onCreated }: AddLeadDialogProps) {
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function close() {
    if (saving) return;
    setForm(EMPTY_FORM);
    setError(null);
    onOpenChange(false);
  }

  async function saveLead(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (!form.business_name.trim()) {
      setError("Enter the business name.");
      return;
    }
    if (!form.phone.trim() && !form.email.trim()) {
      setError("Enter a phone number or email so the lead can be contacted.");
      return;
    }
    if (!form.source.trim()) {
      setError("Say where this lead came from.");
      return;
    }

    setSaving(true);
    try {
      const created = await createLead(payloadFor(form));
      setForm(EMPTY_FORM);
      onCreated(created);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not add the lead.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) close();
        else onOpenChange(true);
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add one lead</DialogTitle>
          <DialogDescription>
            Add a business you have already researched. Business name and source are required,
            plus at least one phone number or email. Everything else is optional.
          </DialogDescription>
        </DialogHeader>
        {error && (
          <p role="alert" className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </p>
        )}
        <form onSubmit={saveLead} className="grid gap-4" noValidate>
          <label className="space-y-1.5 text-sm">
            <span className="font-medium">Business name</span>
            <Input
              required
              autoFocus
              value={form.business_name}
              onChange={(event) => setForm({ ...form, business_name: event.target.value })}
            />
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="space-y-1.5 text-sm">
              <span className="font-medium">
                Phone <span className="font-normal text-muted-foreground">(optional)</span>
              </span>
              <Input
                type="tel"
                autoComplete="tel"
                placeholder="0700 000 000"
                value={form.phone}
                onChange={(event) => setForm({ ...form, phone: event.target.value })}
              />
            </label>
            <label className="space-y-1.5 text-sm">
              <span className="font-medium">
                Email <span className="font-normal text-muted-foreground">(optional)</span>
              </span>
              <Input
                type="email"
                autoComplete="email"
                placeholder="owner@example.test"
                value={form.email}
                onChange={(event) => setForm({ ...form, email: event.target.value })}
              />
            </label>
            <label className="space-y-1.5 text-sm">
              <span className="font-medium">
                Sector <span className="font-normal text-muted-foreground">(optional)</span>
              </span>
              <Input
                value={form.sector}
                onChange={(event) => setForm({ ...form, sector: event.target.value })}
              />
            </label>
            <label className="space-y-1.5 text-sm">
              <span className="font-medium">
                Area <span className="font-normal text-muted-foreground">(optional)</span>
              </span>
              <Input
                value={form.area}
                onChange={(event) => setForm({ ...form, area: event.target.value })}
              />
            </label>
            <label className="space-y-1.5 text-sm sm:col-span-2">
              <span className="font-medium">
                Website status{" "}
                <span className="font-normal text-muted-foreground">(optional)</span>
              </span>
              <Input
                placeholder="e.g. no website listed or Facebook page only"
                value={form.website_status}
                onChange={(event) =>
                  setForm({ ...form, website_status: event.target.value })
                }
              />
            </label>
            <label className="space-y-1.5 text-sm">
              <span className="font-medium">Source</span>
              <Input
                required
                value={form.source}
                onChange={(event) => setForm({ ...form, source: event.target.value })}
              />
            </label>
            <label className="space-y-1.5 text-sm">
              <span className="font-medium">
                Source URL{" "}
                <span className="font-normal text-muted-foreground">(optional)</span>
              </span>
              <Input
                type="url"
                placeholder="https://"
                value={form.source_url}
                onChange={(event) => setForm({ ...form, source_url: event.target.value })}
              />
            </label>
            <label className="flex items-center gap-2 self-end pb-2 text-sm sm:col-span-2">
              <input
                type="checkbox"
                checked={form.has_website}
                onChange={(event) =>
                  setForm({ ...form, has_website: event.target.checked })
                }
              />
              Research confirms this business has a website
            </label>
            <label className="flex items-center gap-2 self-end pb-2 text-sm sm:col-span-2">
              <input
                type="checkbox"
                checked={form.whatsapp_capable}
                onChange={(event) =>
                  setForm({ ...form, whatsapp_capable: event.target.checked })
                }
              />
              This number can receive WhatsApp
            </label>
          </div>
          <p className="text-xs leading-relaxed text-muted-foreground">
            The lead starts with compliance checks in review. Adding it does not approve a
            campaign or send a message.
          </p>
          <div className="flex flex-wrap gap-2">
            <Button type="submit" disabled={saving}>
              <Plus className="size-4" aria-hidden="true" />
              {saving ? "Saving…" : "Save lead"}
            </Button>
            <Button type="button" variant="outline" onClick={close} disabled={saving}>
              Cancel
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
