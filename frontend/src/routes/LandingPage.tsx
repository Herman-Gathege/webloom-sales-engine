import { ArrowRight, Building2, CheckCircle2, ClipboardCheck, Eye, MessageSquare, Search, ShieldCheck, Target, Users } from "lucide-react";
import { Link } from "react-router-dom";

import { MarketingFooter, MarketingNav } from "@/components/layout/MarketingNav";
import { Scout } from "@/components/Scout";
import { type ScoutMood } from "@/components/Scout";
import { DoodleReveal } from "@/components/guidance/Doodle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const benefits = [
  {
    title: "Prospect organisation",
    description:
      "Keep researched businesses, contact routes and source context in one structured lead desk.",
    icon: Building2,
  },
  {
    title: "Outreach management",
    description:
      "Prepare reusable offers and messages without rebuilding the same work for every prospect.",
    icon: MessageSquare,
  },
  {
    title: "Lead prioritisation",
    description:
      "See which prospects are ready to consider, which need evidence and which should not be contacted.",
    icon: Target,
  },
  {
    title: "Team visibility",
    description:
      "Give the team a shared picture of lead status, activity and the next useful conversation.",
    icon: Users,
  },
];

const workflow = [
  {
    title: "Bring in prospects",
    description: "Import researched businesses as leads and keep their source context.",
    icon: Search,
  },
  {
    title: "Organise lead information",
    description: "Keep contact details, source context and research together on the Lead Desk.",
    icon: ClipboardCheck,
  },
  {
    title: "Check outreach eligibility",
    description: "Wadi reviews each lead against outreach policy and suppression before it's used.",
    icon: ShieldCheck,
  },
  {
    title: "Select offers and templates",
    description: "Choose an offer and a message template that shape what the campaign says.",
    icon: MessageSquare,
  },
  {
    title: "Prepare campaign drafts",
    description: "Generate one immutable draft per eligible lead. Nothing is sent until approved.",
    icon: Eye,
  },
];

const problems = [
  {
    title: "Scattered prospect information",
    description:
      "Business details, contact routes and research live across notes, emails and memory instead of one place.",
  },
  {
    title: "Inconsistent follow-ups",
    description:
      "It's hard to tell who was contacted, what was promised and who still needs a conversation.",
  },
  {
    title: "Poor visibility",
    description:
      "The team can't see lead status or who owns the next step, so worthwhile leads go cold.",
  },
  {
    title: "Hard to spot promising opportunities",
    description:
      "Without eligibility and source context, it's unclear which prospects are worth pursuing.",
  },
];

const demoLeads = [
  {
    business: "Mwangaza Opticians",
    area: "Nairobi CBD",
    status: "SMS eligible",
    tone: "eligible" as const,
  },
  {
    business: "Green Valley Agrovet",
    area: "Kiambu Road",
    status: "Needs review",
    tone: "review" as const,
  },
  {
    business: "Riverside Dental Centre",
    area: "Westlands",
    status: "Contact unavailable",
    tone: "muted" as const,
  },
];

function ProductPreview() {
  return (
    <div className="relative">
      <div className="absolute -inset-8 -z-10 rounded-full bg-[var(--wadi-accent)]/20 blur-3xl" />
      <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-[0_30px_80px_rgba(6,51,38,0.16)]">
        <div className="flex items-center justify-between border-b border-border bg-muted/50 px-4 py-3">
          <div className="flex items-center gap-1.5" aria-hidden="true">
            <span className="size-2.5 rounded-full bg-[var(--wadi-sand)]" />
            <span className="size-2.5 rounded-full bg-[var(--wadi-accent)]" />
            <span className="size-2.5 rounded-full bg-[var(--wadi-teal)]" />
          </div>
          <Badge variant="outline" className="bg-background/90 text-[var(--wadi-ink-soft)]">
            Demonstration data
          </Badge>
        </div>

        <div className="grid min-h-[22rem] sm:grid-cols-[7rem_1fr]">
          <div className="hidden border-r border-border bg-[var(--wadi-brand-deep)] p-3 text-white sm:block">
            <p className="rounded-md bg-white/10 px-2.5 py-2 text-xs font-semibold">Leads</p>
            <p className="mt-2 px-2.5 py-2 text-xs text-white/55">Import</p>
            <p className="px-2.5 py-2 text-xs text-white/55">Offers</p>
            <p className="px-2.5 py-2 text-xs text-white/55">Templates</p>
          </div>

          <div className="p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">
                  Lead Desk
                </p>
                <h2 className="mt-1 text-xl">Your working pipeline</h2>
              </div>
              <span className="rounded-md border border-border px-2.5 py-1.5 text-xs text-muted-foreground">
                Search
              </span>
            </div>

            <div className="mt-4 space-y-2">
              {demoLeads.map((lead) => (
                <div
                  key={lead.business}
                  className="flex items-center justify-between gap-3 rounded-xl border border-border bg-background/70 p-3"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{lead.business}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{lead.area}</p>
                  </div>
                  <Badge
                    variant="outline"
                    className={
                      lead.tone === "eligible"
                        ? "border-emerald-300 bg-emerald-50 text-emerald-800"
                        : lead.tone === "review"
                          ? "border-amber-300 bg-amber-50 text-amber-800"
                          : "border-slate-300 bg-slate-50 text-slate-700"
                    }
                  >
                    {lead.status}
                  </Badge>
                </div>
              ))}
            </div>

            <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
              <div className="rounded-lg bg-secondary p-3">
                <CheckCircle2 className="size-4 text-primary" />
                <p className="mt-2 font-medium">Source captured</p>
                <p className="mt-1 text-muted-foreground">Research stays traceable.</p>
              </div>
              <div className="rounded-lg bg-[var(--wadi-sand)]/20 p-3">
                <ShieldCheck className="size-4 text-[var(--wadi-brand)]" />
                <p className="mt-2 font-medium">Responsible outreach</p>
                <p className="mt-1 text-muted-foreground">The team keeps control.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ScoutNote({
  mood,
  message,
  size = 44,
  className,
}: {
  mood: ScoutMood;
  message: string;
  size?: number;
  className?: string;
}) {
  return (
    <div className={["flex items-start gap-3", className].filter(Boolean).join(" ")}>
      <Scout mood={mood} size={size} />
      <p className="text-sm leading-relaxed text-muted-foreground">{message}</p>
    </div>
  );
}

export function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <a
        href="#main-content"
        className="sr-only z-50 rounded-md bg-background px-4 py-2 font-medium focus:not-sr-only focus:fixed focus:top-3 focus:left-3"
      >
        Skip to main content
      </a>
      <MarketingNav />

      <main id="main-content">
        {/* Hero */}
        <section className="relative overflow-hidden">
          <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[34rem] bg-[radial-gradient(circle_at_82%_18%,rgba(180,214,101,0.28),transparent_34rem)]" />
          <div className="mx-auto grid w-full max-w-6xl items-center gap-10 px-4 pt-12 pb-14 sm:px-6 sm:pt-16 lg:grid-cols-[1.05fr_0.95fr] lg:px-8 lg:pt-20 lg:pb-20">
            <div className="space-y-6">
              <Badge className="bg-secondary text-secondary-foreground hover:bg-secondary">
                Built for structured business development
              </Badge>
              <h1
                aria-label="Find the right prospects. Build better conversations."
                className="mt-5 max-w-3xl text-[2.45rem] leading-[1.03] sm:text-5xl lg:text-[4.1rem]"
              >
                Find the right prospects.
                <span className="block text-primary">Build better conversations.</span>
              </h1>
              <div className="mt-3 text-center">
                <DoodleReveal
                  variant="scribble-underline"
                  size={250}
                  className="text-primary/45"
                />
              </div>
              <p className="mt-5 max-w-2xl text-base leading-relaxed text-muted-foreground sm:text-lg">
                Wadi helps your team organise business prospects, understand their potential and
                manage outreach from one workspace and prepare responsible conversations, not
                send them automatically.
              </p>
              <div className="mt-7 flex flex-col gap-3 sm:flex-row">
                <div className="mx-auto mb-2">
                  <DoodleReveal
                    variant="directional-arrow"
                    direction="down"
                    size={34}
                    className="text-primary/50"
                  />
                </div>
                <Button asChild size="lg" className="min-h-12 px-6 text-base">
                  <Link to="/login">
                    Get started
                    <ArrowRight className="size-4" aria-hidden="true" />
                  </Link>
                </Button>
                <Button asChild variant="outline" size="lg" className="min-h-12 px-6 text-base">
                  <Link to="/workflow">Explore the workflow</Link>
                </Button>
              </div>
              <p className="mt-5 text-sm text-muted-foreground">
                Research, review and preparation stay visible. People still make the important
                outreach decisions.
              </p>
            </div>

            <div className="relative">
            <ScoutNote
              mood="idle"
              message="Hi! I'm Wadi. I'll point out the useful bits as you look around."
            />
            <DoodleReveal
              variant="curved-arrow"
              size={96}
              className="absolute -right-8 -bottom-8 text-primary/60"
              direction="right"
            />
              <ProductPreview />
              <DoodleReveal
                variant="curved-arrow"
                size={96}
                className="absolute -right-8 -bottom-8 text-primary/60"
                direction="right"
              />
            </div>
          </div>
        </section>

        {/* The problem */}
        <section id="the-problem" className="border-y border-border bg-card/70 py-16 sm:py-20">
          <div className="mx-auto w-full max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="max-w-2xl">
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-primary">
                The problem
              </p>
              <h2 className="mt-3 text-3xl sm:text-4xl">
                Prospect work is scattered, and follow-ups slip through the cracks.
              </h2>
              <div className="mt-3 text-center">
                <DoodleReveal
                  variant="scribble-underline"
                  size={220}
                  className="text-primary/40"
                />
              </div>
              <p className="mt-4 text-muted-foreground">
                Research, contacts and promises live in different places, so the team spends more
                time reconstructing information than moving conversations forward.
              </p>
            </div>
            <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {problems.map((problem) => (
                <Card key={problem.title} className="bg-background/80">
                  <CardContent className="p-5">
                    <h3 className="text-base font-semibold">{problem.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                      {problem.description}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
            <ScoutNote
              mood="idle"
              message="Contacts, promises and research scattered across tools — this is the mess Wadi clears up."
              className="mt-10"
            />
          </div>
        </section>

        {/* The solution */}
        <section id="the-solution" className="py-16 sm:py-20">
          <div className="mx-auto w-full max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="max-w-2xl">
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-primary">
                The solution
              </p>
              <h2 className="mt-3 text-3xl sm:text-4xl">
                One structured workspace for your prospects.
              </h2>
              <div className="mt-3 text-center">
                <DoodleReveal
                  variant="scribble-underline"
                  size={220}
                  className="text-primary/40"
                />
              </div>
              <p className="mt-4 text-muted-foreground">
                Wadi brings researched businesses, contact routes and source context together so
                the team can prioritise leads and prepare outreach that's ready for a person to
                review and send.
              </p>
            </div>
            <ScoutNote
              mood="success"
              message="A single place for every lead — no more scattered lists."
              className="mt-10"
            />
          </div>
        </section>

        {/* How it works */}
        <section id="how-it-works" className="border-y border-border py-16 sm:py-20">
          <div className="mx-auto w-full max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
              <div className="max-w-2xl">
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-primary">
                  How it works
                </p>
                <h2 className="mt-3 text-3xl sm:text-4xl">
                  From imported lead to prepared draft.
                </h2>
                <p className="mt-4 text-muted-foreground">
                  Wadi follows the same path every time: bring in prospects, organise them, check
                  eligibility, choose an offer and template, then prepare drafts for review.
                </p>
              </div>
              <Link
                to="/workflow"
                className="inline-flex items-center gap-2 text-sm font-semibold text-primary"
              >
                See the full workflow
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </div>
            <div className="mt-8 text-center">
              <DoodleReveal
                variant="dotted-path"
                size={220}
                className="text-muted-foreground/25"
                animate={false}
              />
            </div>
            <ol className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-5" aria-label="Wadi workflow">
              {workflow.map(({ title, description, icon: Icon }, index) => (
                <li key={title} className="rounded-xl border border-border bg-card p-6">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold tracking-[0.14em] text-muted-foreground">
                      0{index + 1}
                    </span>
                    <Icon className="size-5 text-primary" aria-hidden="true" />
                  </div>
                  <h3 className="mt-5 text-lg font-semibold">{title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {description}
                  </p>
                </li>
              ))}
            </ol>
            {/* <div className="mt-10 flex justify-center">
              <DoodleReveal
                variant="dotted-path"
                size={200}
                className="text-muted-foreground/30"
              />
            </div> */}
            <ScoutNote
              mood="idle"
              message="Each stage prepares the next — nothing is approved or sent until a person says so."
              className="mt-10"
            />
          </div>
        </section>

        {/* Benefits */}
        <section id="benefits" className="py-16 sm:py-20">
          <div className="mx-auto w-full max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="max-w-2xl">
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-primary">
                What you get
              </p>
              <h2 className="mt-3 text-3xl sm:text-4xl">
                Clearer priorities, shared visibility, responsible outreach.
              </h2>
            </div>
            <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {benefits.map(({ title, description, icon: Icon }) => (
                <Card key={title} className="bg-background/80">
                  <CardContent className="p-5">
                    <span className="grid size-10 place-items-center rounded-lg bg-secondary text-primary">
                      <Icon className="size-5" aria-hidden="true" />
                    </span>
                    <h3 className="mt-4 text-base font-semibold">{title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                      {description}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
            <div className="mt-12 relative">
              {/* <DoodleReveal
                variant="hand-drawn-circle"
                size={60}
                className="absolute -top-4 -left-4 text-emerald-700"
              /> */}
              <ScoutNote
                mood="success"
                message="The team works from the same picture of every lead."
                className="mt-10"
              />
            </div>
          </div>
        </section>

        {/* Trust and responsibility */}
        <section className="px-4 pb-16 sm:px-6 sm:pb-20 lg:px-8">
          <div className="mx-auto grid w-full max-w-6xl gap-8 rounded-2xl bg-[var(--wadi-brand-deep)] px-6 py-10 text-white sm:px-9 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <div className="flex items-center gap-2 text-[var(--wadi-accent)]">
                <ShieldCheck className="size-5" aria-hidden="true" />
                <p className="text-xs font-bold uppercase tracking-[0.16em]">
                  Trust and responsible outreach
                </p>
              </div>
              <h2 className="mt-4 max-w-3xl text-3xl text-white sm:text-4xl">
                Structure helps the team stay thoughtful as it grows.
              </h2>
              <p className="mt-4 max-w-3xl text-sm leading-relaxed text-white/75 sm:text-base">
                Wadi keeps research sources, contact context and outreach decisions together.
                Public contact information is not treated as blanket permission, and the team can
                maintain clear exclusions and follow-up ownership.
              </p>
            </div>
            <Link to="/workflow" className="min-h-11 font-semibold text-[var(--wadi-accent)]">
              Understand the safeguards
            </Link>
          </div>
        </section>

        {/* Final CTA */}
        <section className="border-t border-border py-16 sm:py-20">
          <div className="mx-auto max-w-3xl px-4 text-center sm:px-6">
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-primary">
              Start with a clearer workspace
            </p>
            <h2 className="mt-3 text-3xl sm:text-4xl">
              Give every prospect a useful next step.
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-muted-foreground">
              Organise the research, prepare the conversation and keep the team aligned around
              what happens next.
            </p>
            <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:justify-center">
              <Button asChild size="lg" className="min-h-12 px-7 text-base">
                <Link to="/login">
                  Get started
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="min-h-12 px-7 text-base">
                <Link to="/workflow">Explore the workflow</Link>
              </Button>
            </div>
          </div>
        </section>
      </main>

      <MarketingFooter />
    </div>
  );
}
