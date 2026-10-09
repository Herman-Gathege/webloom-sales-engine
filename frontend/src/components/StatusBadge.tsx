import type { LeadStatus } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const LABELS: Record<LeadStatus, string> = {
  new: "New",
  contacted: "Contacted",
  replied: "Replied",
  qualified: "Qualified",
  handed_off: "Handed off",
  proposal: "Proposal",
  won: "Won",
  lost: "Lost",
  no_response: "No response",
  not_interested: "Not interested",
  opted_out: "Opted out",
};

const CLASSES: Record<LeadStatus, string> = {
  new: "border-transparent bg-secondary text-secondary-foreground",
  contacted: "border-transparent bg-sky-100 text-sky-900",
  replied: "border-transparent bg-indigo-100 text-indigo-900",
  qualified: "border-transparent bg-amber-100 text-amber-900",
  handed_off: "border-transparent bg-violet-100 text-violet-900",
  proposal: "border-transparent bg-orange-100 text-orange-900",
  won: "border-transparent bg-emerald-100 text-emerald-900",
  lost: "border-transparent bg-zinc-200 text-zinc-700",
  no_response: "border-transparent bg-zinc-100 text-zinc-600",
  not_interested: "border-transparent bg-rose-100 text-rose-900",
  opted_out: "border-transparent bg-red-200 text-red-900",
};

export function StatusBadge({ status }: { status: LeadStatus }) {
  return (
    <Badge variant="outline" className={cn("font-medium", CLASSES[status])}>
      {LABELS[status]}
    </Badge>
  );
}
