import { apiRequest } from "./client";

export type TemplateChannel = "email" | "sms";

export interface Offer {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  price_min: string | null;
  price_max: string | null;
  currency: string;
  pitch_angle: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MessageTemplate {
  id: string;
  offer_id: string;
  channel: TemplateChannel;
  name: string;
  variant: string;
  body: string;
  variables: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type OfferInput = Omit<Offer, "id" | "created_at" | "updated_at">;
export type TemplateInput = Omit<
  MessageTemplate,
  "id" | "created_at" | "updated_at"
>;

const VARIABLE_TOKEN = /\{\{\s*([a-z][a-z0-9_]*)\s*\}\}/g;

export function variablesInBody(body: string): string[] {
  return [...new Set([...body.matchAll(VARIABLE_TOKEN)].map((match) => match[1]))].sort();
}

export function formatPriceRange(
  min: string | null,
  max: string | null,
  currency: string,
): string {
  if (min === null && max === null) return "Price guidance pending";
  const formatter = new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  });
  if (min !== null && max !== null) {
    if (min === max) return formatter.format(Number(min));
    return `${formatter.format(Number(min))} – ${formatter.format(Number(max))}`;
  }
  return min !== null
    ? `From ${formatter.format(Number(min))}`
    : `Up to ${formatter.format(Number(max))}`;
}

export async function listOffers(includeInactive = false): Promise<Offer[]> {
  const query = includeInactive ? "?include_inactive=true" : "";
  return apiRequest<Offer[]>(`/offers${query}`);
}

export async function createOffer(input: OfferInput): Promise<Offer> {
  return apiRequest<Offer>("/offers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export async function updateOffer(
  id: string,
  input: Partial<OfferInput>,
): Promise<Offer> {
  return apiRequest<Offer>(`/offers/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export async function listTemplates(options: {
  includeInactive?: boolean;
  offerId?: string;
  channel?: TemplateChannel;
} = {}): Promise<MessageTemplate[]> {
  const params = new URLSearchParams();
  if (options.includeInactive) params.set("include_inactive", "true");
  if (options.offerId) params.set("offer_id", options.offerId);
  if (options.channel) params.set("channel", options.channel);
  const query = params.size > 0 ? `?${params}` : "";
  return apiRequest<MessageTemplate[]>(`/templates${query}`);
}

export async function createTemplate(input: TemplateInput): Promise<MessageTemplate> {
  return apiRequest<MessageTemplate>("/templates", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export async function updateTemplate(
  id: string,
  input: Partial<TemplateInput>,
): Promise<MessageTemplate> {
  return apiRequest<MessageTemplate>(`/templates/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}
