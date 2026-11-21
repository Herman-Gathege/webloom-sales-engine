import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { listCampaigns, type CampaignSummary } from "@/api/campaign";
import { Scout } from "@/components/Scout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

function statusClass(status: CampaignSummary["status"]): string {
  if (status === "archived") return "border-slate-300 bg-slate-50 text-slate-700";
  if (status === "generated") return "border-emerald-300 bg-emerald-50 text-emerald-800";
  return "border-amber-300 bg-amber-50 text-amber-800";
}

export function CampaignList() {
  const [params, setParams] = useSearchParams();
  const includeArchived = params.get("archived") === "true";
  const [campaigns, setCampaigns] = useState<CampaignSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listCampaigns(includeArchived)
      .then((response) => {
        if (!cancelled) {
          setCampaigns(response.items);
          setError(null);
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "Could not load campaigns.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [includeArchived]);

  function setArchived(next: boolean) {
    const nextParams = new URLSearchParams(params);
    if (next) nextParams.set("archived", "true");
    else nextParams.delete("archived");
    setParams(nextParams, { replace: true });
  }

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader className="flex-row items-start justify-between gap-4">
          <div>
            <CardTitle>Campaigns</CardTitle>
            <CardDescription>
              Prepare SMS drafts from explicitly selected leads. Drafts are never sent here.
            </CardDescription>
          </div>
          <Button asChild size="sm">
            <Link to="/campaigns/new">
              <Plus className="size-4" aria-hidden="true" />
              New campaign
            </Link>
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={includeArchived}
              onChange={(event) => setArchived(event.target.checked)}
            />
            Show archived campaigns
          </label>
          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
          {!campaigns && !error && (
            <p className="text-sm text-muted-foreground">Loading campaigns…</p>
          )}
          {campaigns?.length === 0 && (
            <div className="rounded-xl border border-dashed p-6 text-sm text-muted-foreground">
              <div className="flex items-start gap-3">
                <Scout size={40} />
                <div className="min-w-0">
                  <p className="font-medium text-foreground">No campaigns yet.</p>
                  <p className="mt-1">
                    A campaign gathers the leads you want to reach and prepares one draft per
                    eligible lead. Before creating one, import some leads and check their outreach
                    eligibility from the Lead Desk.
                  </p>
                  <p className="mt-1">
                    Next step:{" "}
                    <Link to="/campaigns/new" className="text-primary font-medium">
                      Create your first campaign
                    </Link>
                    .
                  </p>
                </div>
              </div>
            </div>
          )}
          {campaigns && campaigns.length > 0 && (
            <div className="grid gap-3 md:grid-cols-2">
              {campaigns.map((campaign) => (
                <Link
                  key={campaign.id}
                  to={`/campaigns/${campaign.id}`}
                  className="rounded-xl border border-border bg-card p-4 transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h2 className="font-semibold">{campaign.name}</h2>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {campaign.offer_name} · {campaign.template_name}
                      </p>
                    </div>
                    <Badge variant="outline" className={statusClass(campaign.status)}>
                      {campaign.status}
                    </Badge>
                  </div>
                  <p className="mt-3 line-clamp-2 text-sm text-muted-foreground">
                    {campaign.goal}
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2 text-xs text-muted-foreground">
                    <span>{campaign.selected_count} selected</span>
                    <span>·</span>
                    <span>{campaign.draft_count} drafts</span>
                    <span>·</span>
                    <span>{campaign.skip_count} skipped</span>
                    <span>·</span>
                    <span>{campaign.owner_email}</span>
                    <span>·</span>
                    <span>Updated {new Date(campaign.last_activity_at).toLocaleDateString()}</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
