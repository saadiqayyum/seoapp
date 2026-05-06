import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, Target, ArrowRight, Lightbulb } from "lucide-react";
import type { CompetitorInsight, InsightSeverity } from "@/lib/types";
import { INSIGHT_CATEGORY_LABELS } from "@/lib/constants";
import { cn } from "@/lib/utils";

interface CompetitorInsightsCardProps {
  insights: CompetitorInsight[];
}

const SEVERITY_STYLES: Record<
  InsightSeverity,
  { stripe: string; dot: string; label: string; rank: number }
> = {
  high: {
    stripe: "before:bg-red-500 dark:before:bg-red-400",
    dot: "bg-red-500 dark:bg-red-400",
    label: "text-red-700 dark:text-red-300",
    rank: 0,
  },
  medium: {
    stripe: "before:bg-amber-500 dark:before:bg-amber-400",
    dot: "bg-amber-500 dark:bg-amber-400",
    label: "text-amber-700 dark:text-amber-300",
    rank: 1,
  },
  low: {
    stripe: "before:bg-muted-foreground/40",
    dot: "bg-muted-foreground/60",
    label: "text-muted-foreground",
    rank: 2,
  },
};

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

  const sorted = [...insights].sort(
    (a, b) => SEVERITY_STYLES[a.severity].rank - SEVERITY_STYLES[b.severity].rank,
  );

  const counts = {
    high: insights.filter((i) => i.severity === "high").length,
    medium: insights.filter((i) => i.severity === "medium").length,
    low: insights.filter((i) => i.severity === "low").length,
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between gap-3 text-sm font-medium">
          <span className="flex items-center gap-2">
            <Target className="h-4 w-4" />
            Competitor-Grounded Insights
          </span>
          <SeveritySummary counts={counts} />
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="mb-5 text-xs text-muted-foreground">
          Structural deltas derived from scraping the top-ranking pages. Every
          recommendation cites per-competitor measurements.
        </p>
        <div className="space-y-3">
          {sorted.map((insight, i) => (
            <InsightRow key={`${insight.category}-${i}`} insight={insight} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function SeveritySummary({
  counts,
}: {
  counts: { high: number; medium: number; low: number };
}) {
  return (
    <div className="flex items-center gap-3 text-[11px] font-medium tabular-nums">
      {counts.high > 0 && (
        <span className="flex items-center gap-1.5 text-red-600 dark:text-red-400">
          <span className="h-1.5 w-1.5 rounded-full bg-red-500 dark:bg-red-400" />
          {counts.high} high
        </span>
      )}
      {counts.medium > 0 && (
        <span className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-500 dark:bg-amber-400" />
          {counts.medium} medium
        </span>
      )}
      {counts.low > 0 && (
        <span className="flex items-center gap-1.5 text-muted-foreground">
          <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/60" />
          {counts.low} low
        </span>
      )}
    </div>
  );
}

function InsightRow({ insight }: { insight: CompetitorInsight }) {
  const sev = SEVERITY_STYLES[insight.severity];

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-lg border bg-card pl-5 pr-4 py-4",
        "before:absolute before:left-0 before:top-0 before:h-full before:w-1",
        sev.stripe,
      )}
    >
      {/* Header row: category label + severity */}
      <div className="flex items-center justify-between gap-3">
        <span className="text-[11px] font-bold uppercase tracking-[0.08em] text-foreground/70">
          {INSIGHT_CATEGORY_LABELS[insight.category] ?? insight.category}
        </span>
        <span className={cn("flex items-center gap-1.5 text-[11px] font-semibold", sev.label)}>
          <span className={cn("h-1.5 w-1.5 rounded-full", sev.dot)} />
          {insight.severity}
        </span>
      </div>

      {/* Observation — primary statement */}
      <p className="mt-1.5 text-[15px] font-medium leading-snug text-foreground">
        {insight.observation}
      </p>

      {/* You vs competitors — inline metric comparison */}
      <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1.5 text-sm">
        <div className="flex items-baseline gap-2">
          <span className="text-xs uppercase tracking-wide text-muted-foreground">
            You
          </span>
          <span className="font-semibold tabular-nums">{insight.your_value}</span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-xs uppercase tracking-wide text-muted-foreground">
            Competitors
          </span>
          <span className="font-semibold tabular-nums text-emerald-700 dark:text-emerald-400">
            {insight.competitor_avg}
          </span>
        </div>
      </div>

      {/* Recommendation — primary callout */}
      <div className="mt-3 flex gap-2.5 rounded-md border border-primary/15 bg-primary/5 px-3 py-2.5">
        <Lightbulb className="mt-0.5 h-4 w-4 flex-shrink-0 text-primary" />
        <p className="text-sm leading-relaxed text-foreground">
          {insight.recommendation}
        </p>
      </div>

      {/* Per-competitor evidence — quiet inline list */}
      {insight.evidence.length > 0 && (
        <div className="mt-3 flex flex-wrap items-center gap-x-1 gap-y-1.5 text-xs text-muted-foreground">
          <span className="mr-1 text-[10px] font-bold uppercase tracking-[0.08em]">
            Evidence
          </span>
          {insight.evidence.map((e, i) => (
            <span key={e.competitor_url} className="flex items-center gap-1">
              {i > 0 && <span className="text-muted-foreground/40">·</span>}
              <span className="text-foreground/80">{e.competitor_domain}</span>
              <span className="font-mono tabular-nums text-foreground">
                {e.value}
              </span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
