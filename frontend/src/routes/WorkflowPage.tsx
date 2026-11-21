import { ArrowRight, CheckCircle2, ClipboardCheck, Eye, MessageSquare, Search, ShieldCheck, Target } from "lucide-react";
import { Link } from "react-router-dom";

import { MarketingFooter, MarketingNav } from "@/components/layout/MarketingNav";
import { Scout } from "@/components/Scout";
import { DoodleReveal } from "@/components/guidance/Doodle";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface WorkflowStep {
  title: string;
  whatYouDo: string;
  whatWadiDoes: string;
  whyItMatters: string;
  icon: React.ElementType;
  status: "available" | "coming-soon";
}

const steps: WorkflowStep[] = [
  {
    title: "Import prospect information",
    whatYouDo: "Upload a CSV of researched businesses, or add a lead by hand.",
    whatWadiDoes: "Keeps each lead's source, contact details and collection context together from the start.",
    whyItMatters: "Prospect information stops living across notes, emails and memory.",
    icon: Search,
    status: "available",
  },
  {
    title: "Organise leads",
    whatYouDo: "Review the Lead Desk, filter by sector, area or source, and spot duplicates.",
    whatWadiDoes: "Holds contact details, website observations and research attached to the right prospect.",
    whyItMatters: "The team works from one structured list instead of scattered spreadsheets.",
    icon: ClipboardCheck,
    status: "available",
  },
  {
    title: "Understand lead sources and information",
    whatYouDo: "Open a lead to see where it came from, when it was collected and what research exists.",
    whatWadiDoes: "Stores source name, source URL, collection date and method with every lead.",
    whyItMatters: "You can judge whether a contact is worth pursuing before you invest time in it.",
    icon: Eye,
    status: "available",
  },
  {
    title: "Apply outreach eligibility and compliance checks",
    whatYouDo: "Review each lead's compliance status — eligible, needs review, blocked or invalid.",
    whatWadiDoes: "Checks every lead against outreach policy, suppression and opt-out records before it's used.",
    whyItMatters: "Public contact information is not blanket permission to market.",
    icon: ShieldCheck,
    status: "available",
  },
  {
    title: "Select offers and templates",
    whatYouDo: "Choose an active offer and an approved message template for a campaign.",
    whatWadiDoes: "Snapshots the offer and template content so drafts stay consistent even if the catalogue changes later.",
    whyItMatters: "Every campaign says the right thing, with the right price and pitch.",
    icon: MessageSquare,
    status: "available",
  },
  {
    title: "Prepare campaign drafts",
    whatYouDo: "Select up to 200 eligible leads and generate one immutable draft per lead.",
    whatWadiDoes: "Renders each draft, skips ineligible leads with a reason, and freezes nothing until a person approves it.",
    whyItMatters: "Nothing is sent automatically — a person reviews and approves every outreach decision.",
    icon: Target,
    status: "available",
  },
];

export function WorkflowPage() {
  return (
    <div className="min-h-screen bg-background">
      <MarketingNav />
      <main>
        <section className="overflow-hidden border-b border-border bg-[radial-gradient(circle_at_80%_10%,rgba(180,214,101,0.2),transparent_25rem)]">
          <div className="relative mx-auto w-full max-w-5xl px-4 py-14 sm:px-6 sm:py-20 lg:px-8">
            <div className="flex items-start gap-3">
              <Scout mood="idle" size={56} />
              <div className="min-w-0">
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-primary">
                  Product workflow
                </p>
                <h1 className="mt-3 max-w-3xl text-4xl sm:text-5xl">How Wadi works</h1>
                <p className="mt-5 max-w-2xl text-lg leading-relaxed text-muted-foreground">
                  Wadi gives the team a shared path from prospect research to a prepared,
                  responsible conversation — nothing is sent until a person approves it.
                </p>
              </div>
            </div>
            {/* Decorative arrow. Anchored to this relative content column and
                clipped by the section's overflow-hidden, so its negative offset
                never widens the page. */}
            <DoodleReveal
              variant="curved-arrow"
              size={96}
              className="absolute -right-8 -bottom-8 text-primary/60"
              direction="right"
              animate={false}
            />
          </div>
        </section>

        <section className="mx-auto w-full max-w-5xl px-4 py-14 sm:px-6 sm:py-18 lg:px-8">
          <ol className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3" aria-label="Wadi workflow">
            {steps.map((step, index) => (
              <li key={step.title} className="rounded-xl border border-border bg-card p-6">
                <Card className="h-full border-none bg-transparent p-0 shadow-none">
                  <CardContent className="p-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold tracking-[0.16em] text-muted-foreground">
                        STEP 0{index + 1}
                      </span>
                      <step.icon className="size-5 text-primary" aria-hidden="true" />
                    </div>
                    <CardHeader className="pt-5 pb-0">
                      <CardTitle className="text-xl">{step.title}</CardTitle>
                    </CardHeader>
                    <dl className="mt-4 space-y-3 text-sm leading-relaxed text-muted-foreground">
                      <div className="flex gap-3">
                        <span className="shrink-0 font-semibold text-primary">You:</span>
                        <p className="min-w-0">{step.whatYouDo}</p>
                      </div>
                      <div className="flex gap-3">
                        <span className="shrink-0 font-semibold text-primary">Wadi:</span>
                        <p className="min-w-0">{step.whatWadiDoes}</p>
                      </div>
                      <div className="flex gap-3 pt-2 border-t border-border/50">
                        <span className="shrink-0 font-semibold text-primary">Why it matters:</span>
                        <p className="min-w-0">{step.whyItMatters}</p>
                      </div>
                    </dl>
                  </CardContent>
                </Card>
                {index < steps.length - 1 && (
                  <DoodleReveal
                    variant="dotted-path"
                    size={48}
                    className="mx-auto text-muted-foreground/30"
                  />
                )}
              </li>
            ))}
          </ol>

          <div className="mt-12 rounded-2xl border border-border bg-secondary/60 p-6 sm:p-8">
            <div className="flex items-start gap-3">
              <Scout mood="success" size={44} />
              <div className="min-w-0">
                <div className="flex items-center gap-2 text-primary">
                  <ShieldCheck className="size-5" aria-hidden="true" />
                  <h2 className="text-xl">Responsible by design</h2>
                </div>
                <p className="mt-3 max-w-3xl leading-relaxed text-muted-foreground">
                  Wadi keeps source context and outreach readiness visible. A public business
                  contact is not automatically permission to market, and people remain
                  responsible for final outreach decisions and conversations.
                </p>
                <div className="mt-5 grid gap-3 text-sm sm:grid-cols-3">
                  {[
                    "Source context stays attached",
                    "Exclusions remain visible",
                    "Human handoff stays explicit",
                  ].map((point) => (
                    <p key={point} className="flex items-center gap-2">
                      <CheckCircle2 className="size-4 text-primary" aria-hidden="true" />
                      {point}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="mt-10 flex flex-col gap-3 sm:flex-row">
            <div className="mx-auto mb-2">
              <DoodleReveal
                variant="directional-arrow"
                direction="down"
                size={30}
                className="text-primary/50"
              />
            </div>
            <Button asChild size="lg" className="min-h-12">
              <Link to="/login">
                Get started
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="min-h-12">
              <Link to="/">Back to overview</Link>
            </Button>
          </div>

          <div className="mt-12 border-t border-border pt-8 text-sm text-muted-foreground">
            <p className="font-medium">What's here now vs what's coming</p>
            <ul className="mt-3 space-y-2 list-disc pl-5">
              <li>
                Import, organisation, source context, eligibility checks, offers, templates and
                draft preparation are available in this release.
              </li>
              <li>
                Approval, scheduling, sending and reply handling arrive in later sprints.
              </li>
            </ul>
          </div>
        </section>
      </main>
      <MarketingFooter />
    </div>
  );
}
