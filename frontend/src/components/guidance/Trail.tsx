import { Check } from "lucide-react";

export interface TrailStopProps {
  number: number;
  title: string;
  description: string;
  complete: boolean;
  current: boolean;
}

/**
 * A single step in a guided, trail-style onboarding flow.
 *
 * Extracted from LeadImport so the same guided pattern can be reused across
 * the campaign onboarding experience without duplicating markup or styling.
 */
export function TrailStop({
  number,
  title,
  description,
  complete,
  current,
}: TrailStopProps) {
  return (
    <li
      aria-current={current ? "step" : undefined}
      className={[
        "flex gap-3 rounded-xl border p-3 transition-[border-color,background-color,box-shadow] duration-300",
        complete
          ? "border-emerald-200 bg-emerald-50/80"
          : current
            ? "border-primary/40 bg-background shadow-sm"
            : "border-border bg-background",
      ].join(" ")}
    >
      <span
        className={[
          "grid size-8 shrink-0 place-items-center rounded-full text-xs font-semibold transition-colors duration-300",
          complete
            ? "bg-emerald-600 text-white"
            : current
              ? "bg-primary text-primary-foreground ring-4 ring-primary/10"
              : "bg-secondary text-secondary-foreground",
        ].join(" ")}
      >
        {complete ? <Check className="size-4" aria-hidden="true" /> : number}
      </span>
      <span className="min-w-0">
        <span className="font-semibold leading-snug text-primary">{title}</span>
        <span className="mt-1 block text-sm leading-snug text-muted-foreground">
          {description}
        </span>
      </span>
    </li>
  );
}

/**
 * The mark shown at the end of a completed trail: a short sequence of drawn
 * checkmarks and a label.
 */
export function CompleteTrailMark() {
  return (
    <div aria-hidden="true" className="mt-3 flex items-center gap-1.5">
      {[0, 1, 2].map((stop) => (
        <span key={stop} className="flex items-center gap-1.5">
          <span
            className="grid size-5 place-items-center rounded-full bg-emerald-600 text-white motion-safe:animate-in motion-safe:zoom-in-50 motion-safe:fade-in-0 motion-safe:duration-300"
            style={{ animationDelay: `${stop * 80}ms` }}
          >
            <Check className="size-3" strokeWidth={3} />
          </span>
          {stop < 2 && (
            <span
              className="h-0.5 w-5 origin-left bg-emerald-400 motion-safe:animate-in motion-safe:fade-in-0 motion-safe:slide-in-from-left-1 motion-safe:duration-300"
              style={{ animationDelay: `${stop * 80 + 40}ms` }}
            />
          )}
        </span>
      ))}
      <span className="ml-1 text-xs font-medium text-emerald-800">
        Map · Trail · Scout
      </span>
    </div>
  );
}
