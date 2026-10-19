import { Upload, Users } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { Scout } from "@/components/Scout";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  // `end` keeps "Leads" from staying lit while you are on the import screen.
  { to: "/leads", label: "Leads", icon: Users, end: true },
  { to: "/leads/import", label: "Import", icon: Upload, end: true },
];

/** Screens that exist in the plan but deliberately not in this sprint. */
const LATER_ITEMS = ["Campaigns", "Replies", "Pipeline"];

/**
 * Each of us gets a colour and one word, so the tool looks like it was made by
 * four people rather than by a company. Swap a tint or a word freely.
 */
const CREW = [
  { initial: "H", name: "Herman", role: "product", tint: "#b4d665" },
  { initial: "M", name: "Mark", role: "rails", tint: "#d9c79a" },
  { initial: "S", name: "Sharon", role: "backend", tint: "#9fd8c8" },
  { initial: "A", name: "Anne", role: "seller", tint: "#e8e2c9" },
];

export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <aside className="hidden w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground md:sticky md:top-0 md:flex md:h-screen md:overflow-y-auto">
        <div className="px-6 py-6">
          <div
            className="text-[26px] leading-none tracking-tight text-white"
            style={{ fontFamily: "var(--wadi-display)" }}
          >
            wadi
          </div>
          <div className="mt-1.5 text-[10px] uppercase tracking-[0.22em] text-sidebar-foreground/45">
            sales scout
          </div>
        </div>

        <nav className="flex flex-col gap-1 px-3">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  "relative flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground/65 hover:bg-white/5 hover:text-sidebar-foreground",
                )
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={cn(
                      "absolute left-0 top-1/2 h-4 w-[3px] -translate-y-1/2 rounded-full bg-sidebar-primary transition-opacity",
                      isActive ? "opacity-100" : "opacity-0",
                    )}
                  />
                  <Icon className="size-4" />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="mt-8 px-6">
          <div className="text-[10px] uppercase tracking-[0.18em] text-sidebar-foreground/35">
            Later sprints
          </div>
          <ul className="mt-2 space-y-1 text-sm text-sidebar-foreground/40">
            {LATER_ITEMS.map((label) => (
              <li key={label}>{label}</li>
            ))}
          </ul>
        </div>

        <div className="mt-auto">
          <div className="flex items-center gap-2 px-5 pb-4">
            {CREW.map((person) => (
              <span
                key={person.initial}
                title={`${person.name} · ${person.role}`}
                className="grid size-6 place-items-center rounded-full text-[10px] font-semibold text-[#063326]"
                style={{ backgroundColor: person.tint }}
              >
                {person.initial}
              </span>
            ))}
            <span className="ml-1 text-[10px] uppercase tracking-[0.16em] text-sidebar-foreground/30">
              crew
            </span>
          </div>

          <div className="flex items-end gap-3 border-t border-sidebar-border px-5 py-4">
            <Scout size={78} />
            <p className="pb-1 text-[11px] leading-snug text-sidebar-foreground/45">
              Reading the ground.
              <br />
              Following the water.
            </p>
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="md:hidden">
          <div className="flex items-center justify-between border-b border-border bg-background px-4 py-3">
            <div className="flex items-baseline gap-2">
              <span
                style={{ fontFamily: "var(--wadi-display)" }}
                className="text-lg leading-none"
              >
                wadi
              </span>
              <span className="text-[9px] uppercase tracking-[0.2em] text-muted-foreground">
                scout
              </span>
            </div>
            <Scout size={42} />
          </div>
          <nav className="flex gap-1 border-b border-border bg-background px-3 py-2">
            {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  cn(
                    "flex flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-secondary text-secondary-foreground"
                      : "text-muted-foreground hover:bg-muted",
                  )
                }
              >
                <Icon className="size-4" />
                {label}
              </NavLink>
            ))}
          </nav>
        </header>

        <main className="flex-1">
          <div className="mx-auto w-full max-w-6xl px-4 py-6 md:px-8 md:py-10">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
