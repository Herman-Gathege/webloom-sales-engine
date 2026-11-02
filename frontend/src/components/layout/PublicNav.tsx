import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

import { Scout } from "@/components/Scout";

export function PublicNav() {
  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/95 backdrop-blur">
      <div className="mx-auto flex min-h-16 w-full max-w-6xl items-center justify-between gap-4 px-4 md:px-8">
        <Link to="/" className="flex items-center gap-2.5" aria-label="Wadi home">
          <Scout size={38} />
          <span className="flex flex-col leading-none">
            <span
              style={{ fontFamily: "var(--wadi-display)" }}
              className="text-lg text-foreground"
            >
              wadi
            </span>
            <span className="mt-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              sales scout
            </span>
          </span>
        </Link>
        <Link
          to="/"
          className="inline-flex min-h-10 items-center gap-2 rounded-md px-3 text-sm font-medium text-primary hover:bg-accent focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
        >
          <ArrowLeft className="size-4" />
          How Wadi works
        </Link>
      </div>
    </header>
  );
}
