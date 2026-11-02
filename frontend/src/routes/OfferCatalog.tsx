import { Pencil, Plus, Power, X } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import {
  createOffer,
  formatPriceRange,
  listOffers,
  updateOffer,
  type Offer,
  type OfferInput,
} from "@/api/catalog";
import { useAuth } from "@/auth/context";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const CURRENCIES = ["KES", "USD", "EUR", "GBP", "ZAR", "UGX", "TZS"];

interface OfferFormState {
  name: string;
  slug: string;
  description: string;
  price_min: string;
  price_max: string;
  currency: string;
  pitch_angle: string;
  is_active: boolean;
}

const EMPTY_FORM: OfferFormState = {
  name: "",
  slug: "",
  description: "",
  price_min: "",
  price_max: "",
  currency: "KES",
  pitch_angle: "",
  is_active: true,
};

function optional(value: string): string | null {
  return value.trim() || null;
}

export function OfferCatalog() {
  const { user } = useAuth();
  const canManage = user?.role === "admin";
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<OfferFormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    listOffers(canManage)
      .then((rows) => {
        if (!cancelled) {
          setOffers(rows);
          setError(null);
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "Could not load offers.");
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
    setForm(EMPTY_FORM);
  }

  function editOffer(offer: Offer) {
    setEditingId(offer.id);
    setFormOpen(true);
    setForm({
      name: offer.name,
      slug: offer.slug,
      description: offer.description ?? "",
      price_min: offer.price_min ?? "",
      price_max: offer.price_max ?? "",
      currency: offer.currency,
      pitch_angle: offer.pitch_angle ?? "",
      is_active: offer.is_active,
    });
  }

  async function saveOffer(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (
      form.price_min &&
      form.price_max &&
      Number(form.price_min) > Number(form.price_max)
    ) {
      setError("Minimum price cannot be greater than maximum price.");
      return;
    }
    const payload: OfferInput = {
      name: form.name.trim(),
      slug: form.slug.trim().toLowerCase(),
      description: optional(form.description),
      price_min: optional(form.price_min),
      price_max: optional(form.price_max),
      currency: form.currency.toUpperCase(),
      pitch_angle: optional(form.pitch_angle),
      is_active: form.is_active,
    };
    setSaving(true);
    try {
      if (editingId) await updateOffer(editingId, payload);
      else await createOffer(payload);
      closeForm();
      const rows = await listOffers(canManage);
      setOffers(rows);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not save the offer.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleOffer(offer: Offer) {
    setError(null);
    try {
      await updateOffer(offer.id, { is_active: !offer.is_active });
      setOffers(await listOffers(canManage));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not update the offer.");
    }
  }

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader className="flex-row items-start justify-between gap-4">
          <div>
            <CardTitle>Offers</CardTitle>
            <CardDescription>
              Website packages and other services Webloom can sell.
            </CardDescription>
          </div>
          {canManage && !formOpen && (
            <Button size="sm" onClick={() => setFormOpen(true)}>
              <Plus className="size-4" />
              New offer
            </Button>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <p role="alert" className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </p>
          )}

          {formOpen && canManage && (
            <form onSubmit={saveOffer} className="rounded-xl border border-border bg-muted/30 p-4">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-base font-semibold">
                  {editingId ? "Edit offer" : "New offer"}
                </h2>
                <Button type="button" size="icon-sm" variant="ghost" onClick={closeForm}>
                  <X className="size-4" />
                  <span className="sr-only">Close form</span>
                </Button>
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <label className="space-y-1 text-sm">
                  <span className="font-medium">Name</span>
                  <Input
                    required
                    value={form.name}
                    onChange={(event) => setForm({ ...form, name: event.target.value })}
                  />
                </label>
                <label className="space-y-1 text-sm">
                  <span className="font-medium">Slug</span>
                  <Input
                    required
                    pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
                    placeholder="starter-website"
                    value={form.slug}
                    onChange={(event) => setForm({ ...form, slug: event.target.value })}
                  />
                </label>
                <label className="space-y-1 text-sm sm:col-span-2">
                  <span className="font-medium">Description</span>
                  <textarea
                    aria-label="Offer description"
                    className="min-h-20 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                    value={form.description}
                    onChange={(event) =>
                      setForm({ ...form, description: event.target.value })
                    }
                  />
                </label>
                <label className="space-y-1 text-sm">
                  <span className="font-medium">Minimum price</span>
                  <Input
                    type="number"
                    min="0"
                    step="0.01"
                    value={form.price_min}
                    onChange={(event) =>
                      setForm({ ...form, price_min: event.target.value })
                    }
                  />
                </label>
                <label className="space-y-1 text-sm">
                  <span className="font-medium">Maximum price</span>
                  <Input
                    type="number"
                    min="0"
                    step="0.01"
                    value={form.price_max}
                    onChange={(event) =>
                      setForm({ ...form, price_max: event.target.value })
                    }
                  />
                </label>
                <label className="space-y-1 text-sm">
                  <span className="font-medium">Currency</span>
                  <select
                    aria-label="Offer currency"
                    className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                    value={form.currency}
                    onChange={(event) => setForm({ ...form, currency: event.target.value })}
                  >
                    {CURRENCIES.map((currency) => (
                      <option key={currency} value={currency}>
                        {currency}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="flex items-end gap-2 pb-2 text-sm">
                  <input
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(event) =>
                      setForm({ ...form, is_active: event.target.checked })
                    }
                  />
                  Active
                </label>
                <label className="space-y-1 text-sm sm:col-span-2">
                  <span className="font-medium">Pitch angle</span>
                  <textarea
                    aria-label="Pitch angle"
                    className="min-h-20 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                    value={form.pitch_angle}
                    onChange={(event) =>
                      setForm({ ...form, pitch_angle: event.target.value })
                    }
                  />
                </label>
              </div>
              <div className="mt-4 flex gap-2">
                <Button type="submit" disabled={saving}>
                  {saving ? "Saving…" : editingId ? "Save changes" : "Create offer"}
                </Button>
                <Button type="button" variant="outline" onClick={closeForm}>
                  Cancel
                </Button>
              </div>
            </form>
          )}

          {loading ? (
            <p className="text-sm text-muted-foreground">Loading offers…</p>
          ) : offers.length === 0 ? (
            <p className="rounded-xl border border-dashed p-6 text-sm text-muted-foreground">
              No offers yet. Run the catalogue seed or create the first offer.
            </p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {offers.map((offer) => (
                <article key={offer.id} className="rounded-xl border border-border bg-card p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h2 className="font-semibold">{offer.name}</h2>
                      <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                        {offer.slug}
                      </p>
                    </div>
                    <Badge variant={offer.is_active ? "secondary" : "outline"}>
                      {offer.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                  <p className="mt-3 text-lg font-semibold">
                    {formatPriceRange(offer.price_min, offer.price_max, offer.currency)}
                  </p>
                  {offer.description && (
                    <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                      {offer.description}
                    </p>
                  )}
                  {offer.pitch_angle && (
                    <p className="mt-3 rounded-lg bg-secondary/60 p-3 text-sm">
                      {offer.pitch_angle}
                    </p>
                  )}
                  {canManage && (
                    <div className="mt-4 flex gap-2">
                      <Button size="sm" variant="outline" onClick={() => editOffer(offer)}>
                        <Pencil className="size-4" />
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => void toggleOffer(offer)}
                      >
                        <Power className="size-4" />
                        {offer.is_active ? "Deactivate" : "Reactivate"}
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
