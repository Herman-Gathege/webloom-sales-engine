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
  // Tinted from the Wadi palette rather than Tailwind's defaults: lime for
  // fresh, teal as a lead warms, sand for the slow ones, deep green for won.
  new: "border-transparent bg-[#eff5e0] text-[#084734]",
  contacted: "border-transparent bg-[#d9efe7] text-[#0d4a3a]",
  replied: "border-transparent bg-[#c9e6d8] text-[#084734]",
  qualified: "border-transparent bg-[#f3e8cc] text-[#5c4515]",
  handed_off: "border-transparent bg-[#cfe0da] text-[#0b3b30]",
  proposal: "border-transparent bg-[#f6e3c9] text-[#6b3f0c]",
  won: "border-transparent bg-[#b4d665] text-[#063326]",
  lost: "border-transparent bg-[#eceeec] text-[#5c6660]",
  no_response: "border-transparent bg-[#f2f4f1] text-[#6a7b72]",
  not_interested: "border-transparent bg-[#f7dedb] text-[#8a1f16]",
  opted_out: "border-transparent bg-[#3d5148] text-white",
};

export function StatusBadge({ status }: { status: LeadStatus }) {
  return (
    <Badge variant="outline" className={cn("font-medium", CLASSES[status])}>
      {LABELS[status]}
    </Badge>
  );
}
