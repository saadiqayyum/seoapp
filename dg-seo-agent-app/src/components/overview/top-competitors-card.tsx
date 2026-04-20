import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight } from "lucide-react";

interface TopCompetitorsCardProps {
  competitors: {
    domain: string;
    count: number;
    avgRank: number;
  }[];
}

export function TopCompetitorsCard({ competitors }: TopCompetitorsCardProps) {
  const top5 = competitors.slice(0, 5);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium">Top Competitors</CardTitle>
        <Link
          href="/competitors"
          className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
        >
          View all <ArrowRight className="h-3 w-3" />
        </Link>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {top5.map((comp, i) => (
            <div
              key={comp.domain}
              className="flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-muted text-xs font-bold text-muted-foreground">
                  {i + 1}
                </div>
                <div>
                  <p className="text-sm font-medium">{comp.domain}</p>
                  <p className="text-xs text-muted-foreground">
                    Avg. rank #{comp.avgRank}
                  </p>
                </div>
              </div>
              <Badge variant="secondary">{comp.count} KWs</Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
