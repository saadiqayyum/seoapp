import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { RawCompetitorData } from "@/lib/types";

interface HeadingComparisonProps {
  competitors: RawCompetitorData[];
}

export function HeadingComparison({ competitors }: HeadingComparisonProps) {
  if (competitors.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Competitor Heading Structures
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[320px] pr-4">
          <div className="space-y-5">
            {competitors.map((comp) => {
              const domain = new URL(comp.url).hostname.replace("www.", "");
              return (
                <div key={comp.url} className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold">{domain}</span>
                    <Badge variant="outline" className="text-[10px]">
                      {comp.word_count.toLocaleString()} words
                    </Badge>
                    {comp.has_schema && (
                      <Badge
                        variant="secondary"
                        className="text-[10px] bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400"
                      >
                        Schema
                      </Badge>
                    )}
                  </div>
                  <div className="ml-2 space-y-1 border-l-2 border-muted pl-3">
                    {comp.h1.map((h, i) => (
                      <p
                        key={`h1-${i}`}
                        className="text-sm font-semibold text-foreground"
                      >
                        <span className="mr-1.5 text-[10px] font-bold text-primary">
                          H1
                        </span>
                        {h}
                      </p>
                    ))}
                    {comp.h2.map((h, i) => (
                      <p
                        key={`h2-${i}`}
                        className="text-sm text-foreground/80"
                      >
                        <span className="mr-1.5 text-[10px] font-bold text-muted-foreground">
                          H2
                        </span>
                        {h}
                      </p>
                    ))}
                    {comp.h3.slice(0, 4).map((h, i) => (
                      <p
                        key={`h3-${i}`}
                        className="text-xs text-muted-foreground"
                      >
                        <span className="mr-1.5 text-[10px] font-medium">
                          H3
                        </span>
                        {h}
                      </p>
                    ))}
                    {comp.h3.length > 4 && (
                      <p className="text-xs text-muted-foreground/60">
                        +{comp.h3.length - 4} more H3s
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
