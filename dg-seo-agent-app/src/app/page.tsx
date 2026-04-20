import { Header } from "@/components/layout/header";
import { SummaryCards } from "@/components/overview/summary-cards";
import { HealthScoreGauge } from "@/components/overview/health-score-gauge";
import { RankDistributionChart } from "@/components/overview/rank-distribution-chart";
import { KeywordsTablePreview } from "@/components/overview/keywords-table-preview";
import { SerpFeaturesSummary } from "@/components/overview/serp-features-summary";
import { TopCompetitorsCard } from "@/components/overview/top-competitors-card";
import { getSignedInUserState } from "@/lib/data";
import { EmptyState } from "@/components/layout/empty-state";
import {
  computeHealthScore,
  aggregateSerpFeatures,
  aggregateCompetitors,
} from "@/lib/computations";
import { Badge } from "@/components/ui/badge";
import { Globe } from "lucide-react";

export default async function OverviewPage() {
  const state = await getSignedInUserState();

  if (state.state === "no-domain") {
    return <EmptyState state="no-domain" />;
  }
  if (state.state === "no-audit") {
    return (
      <EmptyState state="no-audit" domainLabel={state.domain.label} />
    );
  }
  if (state.state === "unauthenticated") {
    // Middleware redirects before this renders, but guard defensively
    return null;
  }

  const { report, domain } = state.ctx;
  const healthScore = computeHealthScore(report.keywords);
  const serpFeatures = aggregateSerpFeatures(report.keywords);
  const competitors = aggregateCompetitors(report.keywords);

  return (
    <>
      <Header breadcrumbs={[{ label: "Dashboard" }]} />
      <div className="flex-1 space-y-6 p-4 md:p-6">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">
              SEO Dashboard
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Audit overview for{" "}
              <span className="font-medium text-foreground">
                {domain.label}
              </span>
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1.5">
              <Globe className="h-3 w-3" />
              {report.keywords.length} keywords
            </Badge>
            <Badge variant="secondary">
              {new Date(report.generated_at).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              })}
            </Badge>
          </div>
        </div>

        <SummaryCards keywords={report.keywords} />

        <div className="grid gap-6 lg:grid-cols-5">
          <div className="lg:col-span-3">
            <RankDistributionChart keywords={report.keywords} />
          </div>
          <div className="lg:col-span-2">
            <HealthScoreGauge score={healthScore} />
          </div>
        </div>

        <KeywordsTablePreview keywords={report.keywords} />

        <div className="grid gap-6 lg:grid-cols-2">
          <SerpFeaturesSummary data={serpFeatures} />
          <TopCompetitorsCard competitors={competitors} />
        </div>
      </div>
    </>
  );
}
