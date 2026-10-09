import { Sparkles, Users } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { cn } from "@/lib/utils";

const NAV_ITEMS = [{ to: "/leads", label: "Leads", icon: Users }];

/** Screens that exist in the roadmap but deliberately not in Epic 1. */
const LATER_ITEMS = ["Campaigns", "Replies", "Pipeline"];

export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-muted/30 text-foreground">
      <aside className="hidden w-60 shrink-0 flex-col border-r bg-sidebar text-sidebar-foreground md:flex">
        <div className="flex items-center gap-2 px-5 py-5">
          <Sparkles className="size-5 text-sidebar-primary" />
          <div className="leading-tight">
            <div className="text-sm font-semibold">Webloom</div>
            <div className="text-xs text-muted-foreground">Sales Engine</div>
          </div>
        </div>

        <nav className="flex flex-col gap-1 px-3">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
                )
              }
            >
              <Icon className="size-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-6 px-6">
          <div className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Later blocks
          </div>
          <ul className="mt-2 space-y-1 text-sm text-muted-foreground/70">
            {LATER_ITEMS.map((label) => (
              <li key={label}>{label}</li>
            ))}
          </ul>
        </div>

        <div className="mt-auto px-5 py-5 text-xs text-muted-foreground">
          Epic 1 · first Lego block
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-2 border-b bg-background px-4 py-3 md:hidden">
          <Sparkles className="size-4" />
          <span className="text-sm font-semibold">Webloom Sales Engine</span>
        </header>

        <main className="flex-1">
          <div className="mx-auto w-full max-w-5xl px-4 py-6 md:px-8 md:py-10">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
