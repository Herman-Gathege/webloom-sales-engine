import { ArrowRight, Menu, X } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { Scout } from "@/components/Scout";

export function MarketingNav() {
  const [open, setOpen] = useState(false);

  function closeNavigation() {
    setOpen(false);
  }

  return (
    <header className="sticky top-0 z-40 border-b border-border/80 bg-background/95 backdrop-blur-xl">
      <div className="mx-auto flex min-h-16 w-full max-w-6xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-3" aria-label="Wadi home">
          <Scout size={40} />
          <span className="flex flex-col leading-none">
            <span
              style={{ fontFamily: "var(--wadi-display)" }}
              className="text-xl text-foreground"
            >
              wadi
            </span>
            <span className="mt-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              sales workspace
            </span>
          </span>
        </Link>

        <nav
          className="hidden items-center gap-7 md:flex"
          aria-label="Main navigation"
        >
          <Link
            to="/workflow"
            className="text-sm font-medium text-foreground/75 hover:text-primary"
          >
            How it works
          </Link>
          <Link
            to="/login"
            className="text-sm font-medium text-foreground/75 hover:text-primary"
          >
            Sign in
          </Link>
          <Link
            to="/login"
            className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground shadow-sm transition-transform hover:-translate-y-0.5 focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
          >
            Get started
            <ArrowRight className="size-4" aria-hidden="true" />
          </Link>
        </nav>

        <button
          type="button"
          className="grid size-10 place-items-center rounded-lg border border-border text-foreground md:hidden"
          aria-label={open ? "Close navigation" : "Open navigation"}
          aria-expanded={open}
          aria-controls="marketing-mobile-navigation"
          onClick={() => setOpen((current) => !current)}
        >
          {open ? <X className="size-5" /> : <Menu className="size-5" />}
        </button>
      </div>

      {open && (
        <nav
          id="marketing-mobile-navigation"
          aria-label="Mobile product navigation"
          className="border-t border-border bg-background px-4 py-4 md:hidden"
        >
          <div className="mx-auto flex max-w-6xl flex-col">
            <Link
              to="/workflow"
              onClick={closeNavigation}
              className="rounded-lg px-3 py-3 text-sm font-medium"
            >
              How it works
            </Link>
            <Link
              to="/login"
              onClick={closeNavigation}
              className="rounded-lg px-3 py-3 text-sm font-medium"
            >
              Sign in
            </Link>
            <Link
              to="/login"
              onClick={closeNavigation}
              className="mt-2 inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground"
            >
              Get started
              <ArrowRight className="size-4" aria-hidden="true" />
            </Link>
          </div>
        </nav>
      )}
    </header>
  );
}

export function MarketingFooter() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto grid w-full max-w-6xl gap-8 px-4 py-10 sm:px-6 md:grid-cols-[1fr_auto] md:items-end lg:px-8">
        <div>
          <div className="flex items-center gap-2.5">
            <Scout size={34} />
            <span
              style={{ fontFamily: "var(--wadi-display)" }}
              className="text-xl text-foreground"
            >
              wadi
            </span>
          </div>
          <p className="mt-3 max-w-md text-sm leading-relaxed text-muted-foreground">
            A prospect and outreach workspace by{" "}
            <a
              href="https://webloomtechkenya.com"
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-foreground underline underline-offset-4 transition-colors hover:text-primary"
            >
              webloomtechkenya.com
            </a>
            .
          </p>
        </div>
        <nav
          className="flex flex-wrap gap-x-6 gap-y-3 text-sm"
          aria-label="Footer navigation"
        >
          <Link
            to="/workflow"
            className="text-foreground/75 hover:text-primary"
          >
            How it works
          </Link>
          <Link to="/login" className="text-foreground/75 hover:text-primary">
            Sign in
          </Link>
          <a
            href="https://github.com/Herman-Gathege/webloom-sales-engine/blob/main/docs/full-wadi-documentation.md"
            className="text-foreground/75 hover:text-primary"
          >
            Documentation
          </a>
        </nav>
      </div>
    </footer>
  );
}
