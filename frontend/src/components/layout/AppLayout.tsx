import {
  LogOut,
  Menu,
  ShieldCheck,
  Upload,
  Users as UsersIcon,
  X,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "@/auth/context";
import { CrewList, CrewRail } from "@/components/Crew";
import { Scout } from "@/components/Scout";
import { cn } from "@/lib/utils";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  end: boolean;
  adminOnly?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  // `end` keeps "Leads" from staying lit while you are on the import screen.
  { to: "/leads", label: "Leads", icon: UsersIcon, end: true },
  { to: "/leads/import", label: "Import", icon: Upload, end: true },
  { to: "/admin/users", label: "Users", icon: ShieldCheck, end: true, adminOnly: true },
];

/** Screens that exist in the plan but deliberately not in this sprint. */
const LATER_ITEMS = ["Campaigns", "Replies", "Pipeline"];

function NavItems({ onNavigate }: { onNavigate?: () => void }) {
  const { user } = useAuth();
  const items = NAV_ITEMS.filter((item) => !item.adminOnly || user?.role === "admin");

  return (
    <nav className="flex flex-col gap-1 px-3">
      {items.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNavigate}
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
  );
}

function Account({ onNavigate }: { onNavigate?: () => void }) {
  const { user, logout } = useAuth();
  if (!user) return null;

  return (
    <div className="flex items-center gap-2 px-5 pb-3">
      <div className="min-w-0 flex-1">
        <p className="truncate text-[11px] text-sidebar-foreground/75" title={user.email}>
          {user.email}
        </p>
        <p className="text-[10px] uppercase tracking-[0.16em] text-sidebar-foreground/35">
          {user.role}
        </p>
      </div>
      <button
        type="button"
        aria-label="Sign out"
        onClick={() => {
          void logout();
          onNavigate?.();
        }}
        className="grid size-7 place-items-center rounded-md text-sidebar-foreground/50 transition-colors hover:bg-white/10 hover:text-white"
      >
        <LogOut className="size-4" />
      </button>
    </div>
  );
}

function LaterSprints({ className }: { className?: string }) {
  return (
    <div className={cn("px-6", className)}>
      <div className="text-[10px] uppercase tracking-[0.18em] text-sidebar-foreground/35">
        Later sprints
      </div>
      <ul className="mt-2 space-y-1 text-sm text-sidebar-foreground/40">
        {LATER_ITEMS.map((label) => (
          <li key={label}>{label}</li>
        ))}
      </ul>
    </div>
  );
}

export function AppLayout() {
  const location = useLocation();
  // The drawer remembers the path it was opened on, so any route change closes
  // it without an effect: on a new path, `openedAt` no longer matches.
  const [openedAt, setOpenedAt] = useState<string | null>(null);
  const menuOpen = openedAt === location.pathname;
  const closeMenu = () => setOpenedAt(null);

  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpenedAt(null);
    };
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      {/* Desktop rail: only from 1024px up. Below that, the drawer takes over. */}
      <aside className="hidden w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground lg:sticky lg:top-0 lg:flex lg:h-screen lg:overflow-y-auto">
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

        <NavItems />
        <LaterSprints className="mt-8" />

        <div className="mt-auto">
          <Account />
          <CrewRail />
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
        {/* Mobile and tablet header: Wadi as the logo, menu on the right. */}
        <header className="flex items-center justify-between border-b border-border bg-background px-4 py-3 lg:hidden">
          <Link to="/leads" className="flex items-center gap-2.5">
            <Scout size={40} />
            <span className="flex flex-col leading-none">
              <span
                style={{ fontFamily: "var(--wadi-display)" }}
                className="text-lg text-foreground"
              >
                wadi
              </span>
              <span className="mt-1 text-[9px] uppercase tracking-[0.2em] text-muted-foreground">
                scout
              </span>
            </span>
          </Link>

          <button
            type="button"
            aria-label="Open menu"
            aria-expanded={menuOpen}
            aria-controls="wadi-menu"
            onClick={() => setOpenedAt(location.pathname)}
            className="grid size-9 place-items-center rounded-md text-foreground/70 transition-colors hover:bg-muted hover:text-foreground"
          >
            <Menu className="size-5" />
          </button>
        </header>

        <main className="flex-1">
          <div className="mx-auto w-full max-w-6xl px-4 py-6 md:px-8 md:py-10">
            <Outlet />
          </div>
        </main>
      </div>

      {/* The drawer: same rail, on smaller screens, closed by the backdrop or Esc. */}
      {menuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            aria-hidden="true"
            onClick={() => closeMenu()}
            className="absolute inset-0 animate-in bg-black/40 fade-in"
          />

          <aside
            id="wadi-menu"
            className="absolute inset-y-0 left-0 flex w-72 max-w-[86vw] flex-col bg-sidebar text-sidebar-foreground shadow-xl animate-in duration-200 slide-in-from-left-8"
          >
            <div className="flex items-start justify-between px-5 py-5">
              <Link to="/leads" onClick={() => closeMenu()} className="flex items-center gap-2.5">
                <Scout size={40} />
                <span className="flex flex-col leading-none">
                  <span
                    style={{ fontFamily: "var(--wadi-display)" }}
                    className="text-xl text-white"
                  >
                    wadi
                  </span>
                  <span className="mt-1.5 text-[9px] uppercase tracking-[0.2em] text-sidebar-foreground/45">
                    sales scout
                  </span>
                </span>
              </Link>
              <button
                type="button"
                aria-label="Close menu"
                onClick={() => closeMenu()}
                className="grid size-8 place-items-center rounded-md text-sidebar-foreground/60 transition-colors hover:bg-white/10 hover:text-white"
              >
                <X className="size-4" />
              </button>
            </div>

            <NavItems onNavigate={() => closeMenu()} />
            <LaterSprints className="mt-6" />

            <div className="mt-6">
              <div className="px-6 text-[10px] uppercase tracking-[0.18em] text-sidebar-foreground/35">
                Crew
              </div>
              <div className="mt-2">
                <CrewList />
              </div>
            </div>

            <div className="mt-auto">
              <Account onNavigate={() => setOpenedAt(null)} />
            </div>

            <div className="flex items-end gap-3 border-t border-sidebar-border px-5 py-4">
              <Scout size={56} />
              <p className="pb-1 text-[11px] leading-snug text-sidebar-foreground/45">
                Reading the ground.
                <br />
                Following the water.
              </p>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
