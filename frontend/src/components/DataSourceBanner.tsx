import { Database, FlaskConical } from "lucide-react";

import type { DataSource } from "@/api/types";
import { cn } from "@/lib/utils";

/**
 * Says, on screen, whether this page is showing the real API or bundled sample
 * data, and why. The demo should never leave us guessing whether the backend is
 * actually connected.
 */
export function DataSourceBanner({
  source,
  reason,
}: {
  source: DataSource;
  reason?: string;
}) {
  const isSample = source === "sample";
  const Icon = isSample ? FlaskConical : Database;

  return (
    <div
      role="status"
      className={cn(
        "mb-5 flex items-start gap-2 rounded-md border px-3 py-2 text-sm",
        isSample
          ? "border-amber-300 bg-amber-50 text-amber-900"
          : "bg-card text-muted-foreground",
      )}
    >
      <Icon className="mt-0.5 size-4 shrink-0" />
      {isSample ? (
        <span>
          <strong className="font-semibold">Sample data.</strong> Showing bundled
          fixtures because the Lead API is not connected
          {reason ? ` (${reason})` : ""}. Real data appears the moment Sharon&apos;s
          endpoints answer.
        </span>
      ) : (
        <span>
          <strong className="font-semibold">Live data.</strong> Loaded from the Lead API.
        </span>
      )}
    </div>
  );
}
