import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, Target } from "lucide-react";
import type { CompetitorInsight } from "@/lib/types";
import { INSIGHT_CATEGORY_LABELS, PRIORITY_COLORS } from "@/lib/constants";

interface CompetitorInsightsCardProps {
  insights: CompetitorInsight[];
}

export function CompetitorInsightsCard({
  insights,
}: CompetitorInsightsCardProps) {
  if (insights.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <Target className="h-4 w-4" />
            Competitor-Grounded Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
            <CheckCircle className="h-4 w-4" />
            <p className="text-sm">
              No structural gaps detected versus competitors
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const counts = {
    high: insights.filter((i) => i.severity === "high").length,
    medium: insights.filter((i) => i.severity === "medium").length,
    low: insights.filter((i) => i.severity === "low").length,
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-sm font-medium">
          <span className="flex items-center gap-2">
            <Target className="h-4 w-4" />
            Competitor-Grounded Insights
          </span>
          <div className="flex gap-1.5">
            {counts.high > 0 && (
              <Badge
                variant="secondary"
                className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
              >
                {counts.high} high
              </Badge>
            )}
            {counts.medium > 0 && (
              <Badge
                variant="secondary"
                className="bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300"
              >
                {counts.medium} medium
              </Badge>
            )}
            {counts.low > 0 && (
              <Badge variant="outline">{counts.low} low</Badge>
            )}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="mb-4 text-xs text-muted-foreground">
          Structural deltas derived from scraping the top-ranking pages. Every
          recommendation cites per-competitor measurements.
        </p>
        <div className="space-y-3">
          {insights.map((insight, i) => (
            <InsightRow key={`${insight.category}-${i}`} insight={insight} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function InsightRow({ insight }: { insight: CompetitorInsight }) {
  return (
    <div className="rounded-lg border bg-card/30 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              {INSIGHT_CATEGORY_LABELS[insight.category] ?? insight.category}
            </span>
            <Badge
              variant="secondary"
              className={PRIORITY_COLORS[insight.severity]}
            >
              {insight.severity}
            </Badge>
          </div>
          <p className="text-sm font-medium leading-snug">
            {insight.observation}
          </p>
        </div>
      </div>

      <div className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
        <div className="rounded-md bg-red-50 px-2.5 py-1.5 dark:bg-red-950/40">
          <span className="font-medium text-muted-foreground">You:</span>{" "}
          <span className="font-semibold">{insight.your_value}</span>
        </div>
        <div className="rounded-md bg-emerald-50 px-2.5 py-1.5 dark:bg-emerald-950/40">
          <span className="font-medium text-muted-foreground">
            Competitors:
          </span>{" "}
          <span className="font-semibold">{insight.competitor_avg}</span>
        </div>
      </div>

      <div className="mt-3 rounded-md bg-muted/40 px-3 py-2">
        <p className="text-xs font-medium text-muted-foreground">
          Recommendation
        </p>
        <p className="mt-0.5 text-sm leading-relaxed">
          {insight.recommendation}
        </p>
      </div>

      {insight.evidence.length > 0 && (
        <div className="mt-3">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Per-competitor evidence
          </p>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {insight.evidence.map((e) => (
              <Badge
                key={e.competitor_url}
                variant="outline"
                className="font-normal"
              >
                <span className="text-muted-foreground">
                  {e.competitor_domain}
                </span>
                <span className="mx-1.5 text-muted-foreground/60">·</span>
                <span>{e.value}</span>
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
