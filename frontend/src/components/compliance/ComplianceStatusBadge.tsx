import type { ComplianceStatus } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const LABELS: Record<ComplianceStatus, string> = {
  eligible: "Eligible",
  needs_review: "Needs review",
  blocked: "Blocked",
  invalid: "Invalid / incomplete",
};

const CLASSES: Record<ComplianceStatus, string> = {
  eligible: "border-emerald-300 bg-emerald-50 text-emerald-800",
  needs_review: "border-amber-300 bg-amber-50 text-amber-800",
  blocked: "border-red-300 bg-red-50 text-red-800",
  invalid: "border-slate-300 bg-slate-50 text-slate-700",
};

export function ComplianceStatusBadge({
  status,
  className,
}: {
  status: ComplianceStatus;
  className?: string;
}) {
  return (
    <Badge variant="outline" className={cn("whitespace-nowrap", CLASSES[status], className)}>
      {LABELS[status]}
    </Badge>
  );
}
