"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CompetitorTable } from "@/components/keyword-detail/competitor-table";
import { OnPageIssuesList } from "@/components/keyword-detail/on-page-issues-list";
import { ContentGapsCard } from "@/components/keyword-detail/content-gaps-card";
import { CompetitorInsightsCard } from "@/components/keyword-detail/competitor-insights-card";
import { BacklinkOpportunities } from "@/components/keyword-detail/backlink-opportunities";
import { InternalLinkGauge } from "@/components/keyword-detail/internal-link-gauge";
import { CoreWebVitals } from "@/components/keyword-detail/core-web-vitals";
import { PageSpeedScore } from "@/components/keyword-detail/page-speed-score";
import { PeopleAlsoAsk } from "@/components/keyword-detail/people-also-ask";
import { WordCountChart } from "@/components/keyword-detail/word-count-chart";
import { HeadingComparison } from "@/components/keyword-detail/heading-comparison";
import {
  AlertCircle,
  BookOpen,
  Gauge,
  LayoutGrid,
  Target,
  Users,
} from "lucide-react";
import type { KeywordData } from "@/lib/types";

interface KeywordDetailTabsProps {
  keyword: KeywordData;
}

export function KeywordDetailTabs({ keyword: kw }: KeywordDetailTabsProps) {
  return (
    <Tabs defaultValue="overview" className="space-y-6">
      <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:inline-grid">
        <TabsTrigger value="overview" className="gap-1.5">
          <LayoutGrid className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Overview</span>
        </TabsTrigger>
        <TabsTrigger value="insights" className="gap-1.5">
          <Target className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Insights</span>
        </TabsTrigger>
        <TabsTrigger value="competitors" className="gap-1.5">
          <Users className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Competitors</span>
        </TabsTrigger>
        <TabsTrigger value="content" className="gap-1.5">
          <BookOpen className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Content</span>
        </TabsTrigger>
        <TabsTrigger value="speed" className="gap-1.5">
          <Gauge className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">Speed</span>
        </TabsTrigger>
      </TabsList>

      <TabsContent value="overview" className="space-y-6">
        {/* Quick stats row */}
        <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
          <QuickStat
            label="On-Page Issues"
            value={kw.on_page_issues.length}
            variant={
              kw.on_page_issues.length > 3
                ? "destructive"
                : kw.on_page_issues.length > 0
                  ? "warning"
                  : "success"
            }
          />
          <QuickStat
            label="Content Gaps"
            value={kw.missing_topics.length}
            variant={
              kw.missing_topics.length > 5
                ? "destructive"
                : kw.missing_topics.length > 0
                  ? "warning"
                  : "success"
            }
          />
          <QuickStat
            label="Backlink Gaps"
            value={kw.backlink_gap.length}
            variant={
              kw.backlink_gap.length > 5
                ? "destructive"
                : kw.backlink_gap.length > 0
                  ? "warning"
                  : "success"
            }
          />
          <QuickStat
            label="Internal Links"
            value={`${Math.round(kw.internal_link_score * 100)}%`}
            variant={
              kw.internal_link_score >= 0.7
                ? "success"
                : kw.internal_link_score >= 0.4
                  ? "warning"
                  : "destructive"
            }
          />
        </div>

        <CompetitorInsightsCard insights={kw.competitor_insights} />
        <div className="grid gap-6 lg:grid-cols-2">
          <OnPageIssuesList issues={kw.on_page_issues} />
          <InternalLinkGauge
            score={kw.internal_link_score}
            issues={kw.internal_link_issues}
          />
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <ContentGapsCard topics={kw.missing_topics} />
          <BacklinkOpportunities domains={kw.backlink_gap} />
        </div>
        <PeopleAlsoAsk questions={kw.serp_features.people_also_ask} />
      </TabsContent>

      <TabsContent value="insights" className="space-y-6">
        <CompetitorInsightsCard insights={kw.competitor_insights} />
      </TabsContent>

      <TabsContent value="competitors">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm font-medium">
              Competitor Analysis
              <Badge variant="secondary">
                {kw.top_competitors.length} competitors
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CompetitorTable
              competitors={kw.top_competitors}
              rawData={kw.raw_competitor_data}
            />
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="content" className="space-y-6">
        <div className="grid gap-6 lg:grid-cols-2">
          <WordCountChart competitors={kw.raw_competitor_data} />
          <HeadingComparison competitors={kw.raw_competitor_data} />
        </div>
        <ContentGapsCard topics={kw.missing_topics} />
        <PeopleAlsoAsk questions={kw.serp_features.people_also_ask} />
      </TabsContent>

      <TabsContent value="speed" className="space-y-6">
        {kw.page_speed ? (
          <>
            <div className="flex justify-center">
              <PageSpeedScore score={kw.page_speed.score} />
            </div>
            <CoreWebVitals pageSpeed={kw.page_speed} />
          </>
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center gap-3 py-12">
              <AlertCircle className="h-10 w-10 text-muted-foreground/40" />
              <p className="text-sm text-muted-foreground">
                No page speed data available — this keyword has no ranking page
              </p>
            </CardContent>
          </Card>
        )}
      </TabsContent>
    </Tabs>
  );
}

function QuickStat({
  label,
  value,
  variant,
}: {
  label: string;
  value: string | number;
  variant: "success" | "warning" | "destructive";
}) {
  const colors = {
    success:
      "border-emerald-200 bg-emerald-50/50 dark:border-emerald-900 dark:bg-emerald-950/30",
    warning:
      "border-amber-200 bg-amber-50/50 dark:border-amber-900 dark:bg-amber-950/30",
    destructive:
      "border-red-200 bg-red-50/50 dark:border-red-900 dark:bg-red-950/30",
  };
  const textColors = {
    success: "text-emerald-700 dark:text-emerald-400",
    warning: "text-amber-700 dark:text-amber-400",
    destructive: "text-red-700 dark:text-red-400",
  };

  return (
    <div className={`rounded-lg border px-4 py-3 ${colors[variant]}`}>
      <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      <p className={`text-xl font-bold tabular-nums ${textColors[variant]}`}>
        {value}
      </p>
    </div>
  );
}
