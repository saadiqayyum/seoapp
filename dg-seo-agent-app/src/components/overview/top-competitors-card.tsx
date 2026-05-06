import Link from "next/link";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Users } from "lucide-react";

interface TopCompetitorsCardProps {
  competitors: {
    domain: string;
    count: number;
    avgRank: number;
    keywords: string[];
  }[];
  totalKeywords: number;
}

export function TopCompetitorsCard({
  competitors,
  totalKeywords,
}: TopCompetitorsCardProps) {
  const top5 = competitors.slice(0, 5);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="space-y-0.5">
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <Users className="h-4 w-4" />
            Top Competitors
          </CardTitle>
          <p className="text-xs text-muted-foreground">
            Domains ranking against you across your {totalKeywords} keyword
            {totalKeywords === 1 ? "" : "s"}
          </p>
        </div>
        <Link
          href="/competitors"
          className="inline-flex flex-shrink-0 items-center gap-1 text-xs text-primary hover:underline"
        >
          View all <ArrowRight className="h-3 w-3" />
        </Link>
      </CardHeader>
      <CardContent>
        {top5.length === 0 ? (
          <p className="py-4 text-center text-sm text-muted-foreground">
            No competitor data yet
          </p>
        ) : (
          <ul className="space-y-2.5">
            {top5.map((comp, i) => {
              const sharePct = Math.round((comp.count / totalKeywords) * 100);
              return (
                <li
                  key={comp.domain}
                  className="flex items-center justify-between gap-3"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-muted text-xs font-bold text-muted-foreground">
                      {i + 1}
                    </div>
                    <div className="min-w-0">
                      <a
                        href={`https://${comp.domain}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block truncate text-sm font-medium hover:text-primary hover:underline"
                      >
                        {comp.domain}
                      </a>
                      <p className="text-xs tabular-nums text-muted-foreground">
                        Avg. rank #{comp.avgRank} · ranks for{" "}
                        {comp.count}/{totalKeywords} of your keywords
                      </p>
                    </div>
                  </div>
                  <Badge variant="secondary" className="flex-shrink-0 tabular-nums">
                    {sharePct}%
                  </Badge>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
