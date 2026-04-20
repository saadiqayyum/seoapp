import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BookOpen, CheckCircle, Sparkles, HelpCircle } from "lucide-react";
import type { MissingTopic } from "@/lib/types";

interface ContentGapsCardProps {
  topics: MissingTopic[];
}

function extractDomain(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export function ContentGapsCard({ topics }: ContentGapsCardProps) {
  if (topics.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <BookOpen className="h-4 w-4" />
            Content Gaps
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
            <CheckCircle className="h-4 w-4" />
            <p className="text-sm">No content gaps identified</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const headingGaps = topics.filter((t) => t.kind === "heading");
  const paaGaps = topics.filter((t) => t.kind === "paa");
  const serpGaps = topics.filter((t) => t.kind === "serp_feature");

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-sm font-medium">
          <span className="flex items-center gap-2">
            <BookOpen className="h-4 w-4" />
            Content Gaps
          </span>
          <Badge
            variant="secondary"
            className={
              topics.length > 5
                ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
                : "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300"
            }
          >
            {topics.length} gaps
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {headingGaps.length > 0 && (
          <section className="space-y-2">
            <div className="flex items-center gap-2">
              <BookOpen className="h-3.5 w-3.5 text-muted-foreground" />
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Heading sections to add ({headingGaps.length})
              </h4>
            </div>
            <p className="text-xs text-muted-foreground">
              Sections multiple competitors cover that your page doesn&apos;t.
            </p>
            <ul className="space-y-2">
              {headingGaps.map((t) => (
                <li
                  key={t.topic}
                  className="rounded-md border bg-card/50 px-3 py-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-sm font-medium leading-snug">
                        {t.example_heading}
                      </p>
                      <p className="mt-1 text-[11px] text-muted-foreground">
                        Seen on{" "}
                        {t.source_competitors
                          .slice(0, 3)
                          .map(extractDomain)
                          .join(", ")}
                        {t.source_competitors.length > 3
                          ? ` +${t.source_competitors.length - 3} more`
                          : ""}
                      </p>
                    </div>
                    <Badge variant="outline" className="shrink-0 text-[10px]">
                      {t.level} · {t.frequency}×
                    </Badge>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}

        {paaGaps.length > 0 && (
          <section className="space-y-2">
            <div className="flex items-center gap-2">
              <HelpCircle className="h-3.5 w-3.5 text-muted-foreground" />
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Unanswered PAA questions ({paaGaps.length})
              </h4>
            </div>
            <ul className="space-y-1.5">
              {paaGaps.map((t) => (
                <li
                  key={t.topic}
                  className="rounded-md border border-dashed px-3 py-2 text-sm"
                >
                  {t.topic}
                </li>
              ))}
            </ul>
          </section>
        )}

        {serpGaps.length > 0 && (
          <section className="space-y-2">
            <div className="flex items-center gap-2">
              <Sparkles className="h-3.5 w-3.5 text-muted-foreground" />
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                SERP feature opportunities ({serpGaps.length})
              </h4>
            </div>
            <ul className="space-y-1.5">
              {serpGaps.map((t) => (
                <li
                  key={t.topic}
                  className="rounded-md bg-muted/40 px-3 py-2 text-sm"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span>{t.topic}</span>
                    {t.source_competitors.length > 0 && (
                      <Badge variant="outline" className="shrink-0 text-[10px]">
                        {t.frequency} competitors
                      </Badge>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}
      </CardContent>
    </Card>
  );
}
