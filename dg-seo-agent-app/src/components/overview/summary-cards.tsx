import { Card, CardContent } from "@/components/ui/card";
import { Search, TrendingUp, Zap, Activity } from "lucide-react";
import type { KeywordData } from "@/lib/types";
import { computeHealthScore } from "@/lib/computations";

interface SummaryCardsProps {
  keywords: KeywordData[];
}

export function SummaryCards({ keywords }: SummaryCardsProps) {
  const totalKeywords = keywords.length;
  const rankedKeywords = keywords.filter((kw) => kw.your_rank !== null);
  const avgRank =
    rankedKeywords.length > 0
      ? Math.round(
          rankedKeywords.reduce((sum, kw) => sum + (kw.your_rank ?? 0), 0) /
            rankedKeywords.length
        )
      : null;
  const page1Count = keywords.filter(
    (kw) => kw.your_rank !== null && kw.your_rank <= 10
  ).length;
  const healthScore = computeHealthScore(keywords);

  const cards = [
    {
      title: "Total Keywords",
      value: totalKeywords,
      subtitle: `${rankedKeywords.length} ranking`,
      icon: Search,
      gradient: "from-cyan-500/10 to-teal-500/10",
      iconColor: "text-cyan-600 dark:text-cyan-400",
      iconBg: "bg-cyan-100 dark:bg-cyan-900/50",
    },
    {
      title: "Average Rank",
      value: avgRank !== null ? `#${avgRank}` : "N/A",
      subtitle:
        avgRank !== null && avgRank <= 10
          ? "Page 1 average"
          : avgRank !== null
            ? `Page ${Math.ceil(avgRank / 10)} average`
            : "Not ranking",
      icon: TrendingUp,
      gradient: "from-emerald-500/10 to-teal-500/10",
      iconColor: "text-emerald-600 dark:text-emerald-400",
      iconBg: "bg-emerald-100 dark:bg-emerald-900/50",
    },
    {
      title: "Page 1 Keywords",
      value: `${page1Count}/${totalKeywords}`,
      subtitle:
        page1Count === totalKeywords
          ? "All on page 1"
          : `${totalKeywords - page1Count} need improvement`,
      icon: Zap,
      gradient: "from-amber-500/10 to-orange-500/10",
      iconColor: "text-amber-600 dark:text-amber-400",
      iconBg: "bg-amber-100 dark:bg-amber-900/50",
    },
    {
      title: "Health Score",
      value: `${healthScore}`,
      subtitle:
        healthScore >= 70
          ? "Good overall health"
          : healthScore >= 40
            ? "Needs improvement"
            : "Critical issues found",
      icon: Activity,
      gradient: "from-teal-500/10 to-emerald-500/10",
      iconColor: "text-teal-600 dark:text-teal-400",
      iconBg: "bg-teal-100 dark:bg-teal-900/50",
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.title} className="relative overflow-hidden">
          <div
            className={`absolute inset-0 bg-gradient-to-br ${card.gradient} pointer-events-none`}
          />
          <CardContent className="relative pt-5">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  {card.title}
                </p>
                <p className="text-3xl font-bold tracking-tight">
                  {card.value}
                </p>
                <p className="text-xs text-muted-foreground">{card.subtitle}</p>
              </div>
              <div
                className={`flex h-11 w-11 items-center justify-center rounded-xl ${card.iconBg}`}
              >
                <card.icon className={`h-5 w-5 ${card.iconColor}`} />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
