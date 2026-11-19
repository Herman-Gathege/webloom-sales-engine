import { ArrowRight, CheckCircle2, ClipboardCheck, Eye, MessageSquare, Search, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

import { MarketingFooter, MarketingNav } from "@/components/layout/MarketingNav";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const steps = [
  {
    title: "Find prospects",
    description:
      "Bring researched businesses into one place instead of scattering lists, links and notes across tools.",
    icon: Search,
  },
  {
    title: "Organise lead information",
    description:
      "Keep contact details, source context, website observations and other research attached to the right prospect.",
    icon: ClipboardCheck,
  },
  {
    title: "Prepare outreach",
    description:
      "Select the offer and approved message, review readiness and prepare relevant follow-up work.",
    icon: MessageSquare,
  },
  {
    title: "Track conversations and follow-ups",
    description:
      "Keep the team aligned on activity, ownership and where a person should take over.",
    icon: Eye,
  },
];

export function WorkflowPage() {
  return (
    <div className="min-h-screen bg-background">
      <MarketingNav />
      <main>
        <section className="border-b border-border bg-[radial-gradient(circle_at_80%_10%,rgba(180,214,101,0.2),transparent_25rem)]">
          <div className="mx-auto w-full max-w-5xl px-4 py-14 sm:px-6 sm:py-20 lg:px-8">
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-primary">
              Product workflow
            </p>
            <h1 className="mt-3 max-w-3xl text-4xl sm:text-5xl">How Wadi works</h1>
            <p className="mt-5 max-w-2xl text-lg leading-relaxed text-muted-foreground">
              Wadi gives the team a shared path from prospect research to a prepared, responsible
              conversation.
            </p>
          </div>
        </section>

        <section className="mx-auto w-full max-w-5xl px-4 py-14 sm:px-6 sm:py-18 lg:px-8">
          <ol className="grid gap-4 sm:grid-cols-2">
            {steps.map(({ title, description, icon: Icon }, index) => (
              <li key={title}>
                <Card className="h-full">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold tracking-[0.16em] text-muted-foreground">
                        STEP 0{index + 1}
                      </span>
                      <Icon className="size-5 text-primary" aria-hidden="true" />
                    </div>
                    <h2 className="mt-5 text-xl">{title}</h2>
                    <p className="mt-3 leading-relaxed text-muted-foreground">{description}</p>
                  </CardContent>
                </Card>
              </li>
            ))}
          </ol>

          <div className="mt-8 rounded-2xl border border-border bg-secondary/60 p-6 sm:p-8">
            <div className="flex items-center gap-2 text-primary">
              <ShieldCheck className="size-5" aria-hidden="true" />
              <h2 className="text-xl">Responsible by design</h2>
            </div>
            <p className="mt-3 max-w-3xl leading-relaxed text-muted-foreground">
              Wadi keeps source context and outreach readiness visible. A public business contact
              is not automatically permission to market, and people remain responsible for final
              outreach decisions and conversations.
            </p>
            <div className="mt-5 grid gap-3 text-sm text-foreground sm:grid-cols-3">
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

          <div className="mt-10 flex flex-col gap-3 sm:flex-row">
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
        </section>
      </main>
      <MarketingFooter />
    </div>
  );
}
