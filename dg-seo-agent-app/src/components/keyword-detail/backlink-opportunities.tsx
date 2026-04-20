import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Link2Off } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

interface BacklinkOpportunitiesProps {
  domains: string[];
}

export function BacklinkOpportunities({ domains }: BacklinkOpportunitiesProps) {
  if (domains.length === 0) {
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
          <Badge variant="secondary">{domains.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="mb-3 text-xs text-muted-foreground">
          Domains linking to competitors but not to you
        </p>
        <ScrollArea className={domains.length > 5 ? "h-[200px]" : ""}>
          <div className="space-y-1.5">
            {domains.map((domain, i) => (
              <div
                key={domain}
                className="flex items-center gap-3 rounded-lg border px-3 py-2 transition-colors hover:bg-muted/50"
              >
                <div className="flex h-6 w-6 items-center justify-center rounded-md bg-muted text-[10px] font-bold text-muted-foreground">
                  {i + 1}
                </div>
                <Link2Off className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-sm font-medium">{domain}</span>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
