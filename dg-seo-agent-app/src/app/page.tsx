import { Header } from "@/components/layout/header";
import { SummaryCards } from "@/components/overview/summary-cards";
import { ActionPrioritiesCard } from "@/components/overview/action-priorities-card";
import { RankDistributionChart } from "@/components/overview/rank-distribution-chart";
import { KeywordsTablePreview } from "@/components/overview/keywords-table-preview";
import { SerpFeaturesSummary } from "@/components/overview/serp-features-summary";
import { TopCompetitorsCard } from "@/components/overview/top-competitors-card";
import { getSignedInUserState } from "@/lib/data";
import { getDomainOverview } from "@/lib/audits";
import { EmptyState } from "@/components/layout/empty-state";
import {
  aggregateSerpFeatures,
  aggregateCompetitors,
} from "@/lib/computations";
import { Badge } from "@/components/ui/badge";
import { Search, FileClock, Calendar } from "lucide-react";

function formatRelative(iso: string | null): string {
  if (!iso) return "never";
  const diffMs = Date.now() - new Date(iso).getTime();
  const day = 24 * 60 * 60 * 1000;
  if (diffMs < day) return "today";
  if (diffMs < 2 * day) return "yesterday";
  if (diffMs < 7 * day) return `${Math.floor(diffMs / day)}d ago`;
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default async function OverviewPage() {
  const state = await getSignedInUserState();

  if (state.state === "no-domain") return <EmptyState state="no-domain" />;
  if (state.state === "no-audit")
    return <EmptyState state="no-audit" domainLabel={state.domain.label} />;
  if (state.state === "unauthenticated") return null;

  const { domain, user } = state.ctx;
  const overview = await getDomainOverview(user.userId, domain.id);
  const { keywords, totalAudits, lastCompletedAt } = overview;

  const serpFeatures = aggregateSerpFeatures(keywords);
  const competitors = aggregateCompetitors(keywords);

  return (
    <>
      <Header breadcrumbs={[{ label: "Dashboard" }]} />
      <div className="flex-1 space-y-6 p-4 md:p-6">
        {/* Header: clear scope statement */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">SEO Dashboard</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Overview for{" "}
              <span className="font-medium text-foreground">{domain.label}</span>{" "}
              · aggregated across{" "}
              <span className="font-medium text-foreground">
                {keywords.length}{" "}
                {keywords.length === 1 ? "keyword" : "keywords"}
              </span>{" "}
              from{" "}
              <span className="font-medium text-foreground">
                {totalAudits} {totalAudits === 1 ? "audit" : "audits"}
              </span>
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="gap-1.5">
              <Search className="h-3 w-3" />
              {keywords.length}{" "}
              {keywords.length === 1 ? "keyword" : "keywords"}
            </Badge>
            <Badge variant="outline" className="gap-1.5">
              <FileClock className="h-3 w-3" />
              {totalAudits} {totalAudits === 1 ? "audit" : "audits"}
            </Badge>
            <Badge variant="secondary" className="gap-1.5">
              <Calendar className="h-3 w-3" />
              Last run {formatRelative(lastCompletedAt)}
            </Badge>
          </div>
        </div>

        {/* Row 1 — top-line metrics */}
        <SummaryCards keywords={keywords} />

        {/* Row 2 — performance breakdown */}
        <div className="grid gap-6 lg:grid-cols-5">
          <div className="lg:col-span-3">
            <RankDistributionChart keywords={keywords} />
          </div>
          <div className="lg:col-span-2">
            <ActionPrioritiesCard keywords={keywords} />
          </div>
        </div>

        {/* Row 3 — keyword detail preview */}
        <KeywordsTablePreview keywords={keywords} />

        {/* Row 4 — competitive landscape */}
        <div className="grid gap-6 lg:grid-cols-2">
          <SerpFeaturesSummary
            data={serpFeatures}
            totalKeywords={keywords.length}
          />
          <TopCompetitorsCard
            competitors={competitors}
            totalKeywords={keywords.length}
          />
        </div>
      </div>
    </>
  );
}
