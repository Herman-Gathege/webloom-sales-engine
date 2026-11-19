import { ArrowUpRight, BookOpen, Code2, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const docsBase = "https://github.com/Herman-Gathege/webloom-sales-engine/blob/main";

export function InternalOrientation() {
  return (
    <div className="space-y-5">
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-primary">
          Team-only context
        </p>
        <h1 className="mt-2 text-3xl sm:text-4xl">Internal orientation</h1>
        <p className="mt-3 max-w-3xl text-muted-foreground">
          Where Wadi has come from and where the team is going. Product delivery should use the
          current sprint contract, while the architecture and compliance notes below explain the
          system behind it.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <BookOpen className="size-5 text-primary" aria-hidden="true" />
            <CardTitle>Sprint status</CardTitle>
            <CardDescription>Current team focus</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Badge className="bg-secondary text-secondary-foreground">
              Sprint 5 active
            </Badge>
            <p className="text-muted-foreground">
              Herman implements campaigns, lead selection, preview and draft generation. Mark,
              Sharon and Anne review; approval and sending remain outside the sprint.
            </p>
            <Link to="/leads" className="inline-flex items-center gap-1 font-medium text-primary">
              Open the Lead Desk
              <ArrowUpRight className="size-4" aria-hidden="true" />
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <Code2 className="size-5 text-primary" aria-hidden="true" />
            <CardTitle>Architecture</CardTitle>
            <CardDescription>Application boundaries</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>React workspace → FastAPI → PostgreSQL.</p>
            <p>Leads, provenance, policy decisions, catalogue and audit stay durable.</p>
            <p>FikaTu remains the future delivery boundary; Wadi owns sales state.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <ShieldCheck className="size-5 text-primary" aria-hidden="true" />
            <CardTitle>Responsible outreach</CardTitle>
            <CardDescription>Compliance controls</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>Imports preserve provenance and separate data quality from eligibility.</p>
            <p>Approved rules may qualify a channel; exceptions stay visible.</p>
            <p>Suppression, opt-out and the final human send decision remain authoritative.</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Documentation and roadmap</CardTitle>
          <CardDescription>
            Keep the internal reading path short and move the detail into the source documents.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2">
          {[
            ["Visual workflow", `${docsBase}/docs/workflow.html`],
            ["Stage-by-stage workflow", `${docsBase}/docs/workflow-description.md`],
            ["Full Wadi guide", `${docsBase}/docs/full-wadi-documentation.md`],
            ["Sprint plan", `${docsBase}/docs/delivery/sprint-plan.md`],
            ["Sprint 5 homework", `${docsBase}/docs/homework/sprint-5/README.md`],
            ["Compliance notes", `${docsBase}/docs/compliance/implementation-notes.md`],
          ].map(([label, href]) => (
            <a
              key={label}
              href={href}
              className="flex items-center justify-between gap-3 rounded-lg border border-border px-4 py-3 text-sm font-medium hover:bg-accent"
            >
              {label}
              <ArrowUpRight className="size-4 text-primary" aria-hidden="true" />
            </a>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Roadmap</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 text-sm sm:grid-cols-5">
          {[
            ["S1–4", "Foundation and catalogue"],
            ["S5", "Campaigns and drafts"],
            ["S6", "Approval and delivery"],
            ["S7", "Replies and handoff"],
            ["S8–9", "Learning, pilot and hardening"],
          ].map(([sprint, label]) => (
            <div key={sprint} className="rounded-lg border border-border p-3">
              <p className="font-semibold text-primary">{sprint}</p>
              <p className="mt-1 text-muted-foreground">{label}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
