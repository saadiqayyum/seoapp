"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
import { ExternalLink } from "lucide-react";
import type { RawCompetitorData } from "@/lib/types";

interface WordCountChartProps {
  competitors: RawCompetitorData[];
  yourWordCount?: number;
  yourUrl?: string | null;
}

function pathOf(url: string): string {
  try {
    const u = new URL(url);
    return `${u.pathname}${u.search}` || "/";
  } catch {
    return url;
  }
}

function shortDomain(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

interface ChartRow {
  name: string;
  words: number;
  isYou: boolean;
  url: string | null;
  fullDomain: string | null;
}

export function WordCountChart({
  competitors,
  yourWordCount,
  yourUrl,
}: WordCountChartProps) {
  const data: ChartRow[] = [
    ...(yourWordCount
      ? [
          {
            name: "You",
            words: yourWordCount,
            isYou: true,
            url: yourUrl ?? null,
            fullDomain: yourUrl ? shortDomain(yourUrl) : null,
          },
        ]
      : []),
    ...competitors.map((comp) => {
      const domain = shortDomain(comp.url);
      return {
        name: domain.length > 15 ? domain.slice(0, 15) + "…" : domain,
        words: comp.word_count,
        isYou: false,
        url: comp.url,
        fullDomain: domain,
      };
    }),
  ].sort((a, b) => b.words - a.words);

  const avgWords = competitors.length
    ? Math.round(
        competitors.reduce((sum, c) => sum + c.word_count, 0) /
          competitors.length,
      )
    : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Word Count Comparison
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="h-[250px] w-full">
          <ResponsiveContainer width="100%" height={250} minWidth={200}>
            <BarChart data={data} layout="vertical" margin={{ left: 10 }}>
              <XAxis
                type="number"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: number) =>
                  v >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(v)
                }
              />
              <YAxis
                type="category"
                dataKey="name"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                width={100}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const row = payload[0].payload as ChartRow;
                    return (
                      <div className="max-w-[320px] rounded-lg border bg-background px-3 py-2 shadow-sm">
                        <p className="text-sm font-medium">
                          {row.fullDomain ?? row.name}
                        </p>
                        {row.url && (
                          <p className="break-all text-[11px] text-muted-foreground">
                            {row.url}
                          </p>
                        )}
                        <p className="mt-1 text-sm tabular-nums text-muted-foreground">
                          {(payload[0].value as number).toLocaleString()} words
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              {avgWords > 0 && (
                <ReferenceLine
                  x={avgWords}
                  stroke="#94a3b8"
                  strokeDasharray="4 4"
                  label={{
                    value: `Avg: ${avgWords.toLocaleString()}`,
                    position: "top",
                    fontSize: 10,
                    fill: "#94a3b8",
                  }}
                />
              )}
              <Bar dataKey="words" radius={[0, 4, 4, 0]} barSize={24}>
                {data.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={
                      entry.isYou
                        ? "var(--color-primary)"
                        : "rgba(148, 163, 184, 0.3)"
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Page-link legend — full URLs visible without hovering */}
        <ul className="space-y-1.5 border-t pt-3 text-xs">
          {data.map((row) =>
            row.url ? (
              <li key={`${row.url}-${row.name}`} className="flex items-baseline gap-2">
                <span
                  className={`inline-flex h-2 w-2 flex-shrink-0 translate-y-0.5 rounded-sm ${
                    row.isYou ? "bg-primary" : "bg-slate-300 dark:bg-slate-600"
                  }`}
                />
                <a
                  href={row.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  title={row.url}
                  className="group inline-flex min-w-0 flex-1 flex-wrap items-baseline gap-x-2 transition-colors hover:text-primary"
                >
                  <span className="font-medium">
                    {row.isYou ? "You" : row.fullDomain}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-muted-foreground transition-colors group-hover:text-primary/70">
                    {pathOf(row.url)}
                  </span>
                  <ExternalLink className="h-3 w-3 flex-shrink-0 opacity-0 transition-opacity group-hover:opacity-100" />
                </a>
                <span className="flex-shrink-0 tabular-nums text-muted-foreground">
                  {row.words.toLocaleString()}
                </span>
              </li>
            ) : null,
          )}
        </ul>
      </CardContent>
    </Card>
  );
}
