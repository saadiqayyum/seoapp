import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Link2Off } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { BacklinkGap } from "@/lib/types";

interface BacklinkOpportunitiesProps {
  gaps: BacklinkGap[];
}

function oprBadgeVariant(score: number): "default" | "secondary" | "outline" {
  if (score >= 6) return "default";
  if (score >= 3) return "secondary";
  return "outline";
}

export function BacklinkOpportunities({ gaps }: BacklinkOpportunitiesProps) {
  if (gaps.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <ExternalLink className="h-4 w-4" />
            Backlink Opportunities
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-emerald-600 dark:text-emerald-400">
            No backlink gaps identified
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-sm font-medium">
          <span className="flex items-center gap-2">
            <ExternalLink className="h-4 w-4" />
            Backlink Opportunities
          </span>
          <Badge variant="secondary">{gaps.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="mb-3 text-xs text-muted-foreground">
          Domains linking to competitor URLs ranking for this keyword, but not to yours.
          OPR = OpenPageRank authority (0-10).
        </p>
        <ScrollArea className={gaps.length > 5 ? "h-[260px]" : ""}>
          <div className="space-y-1.5">
            {gaps.map((g, i) => {
              const compCount = g.links_to_competitors.length;
              return (
                <div
                  key={g.source_domain}
                  className="flex items-center gap-3 rounded-lg border px-3 py-2 transition-colors hover:bg-muted/50"
                >
                  <div className="flex h-6 w-6 items-center justify-center rounded-md bg-muted text-[10px] font-bold text-muted-foreground">
                    {i + 1}
                  </div>
                  <Link2Off className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="flex-1 truncate text-sm font-medium">
                    {g.source_domain}
                  </span>
                  <Badge variant={oprBadgeVariant(g.opr_score)} className="tabular-nums">
                    OPR {g.opr_score.toFixed(1)}
                  </Badge>
                  <Badge variant="outline" className="tabular-nums">
                    {compCount} link{compCount === 1 ? "" : "s"}
                  </Badge>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
