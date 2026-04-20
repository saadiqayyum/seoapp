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
import type { RawCompetitorData } from "@/lib/types";

interface WordCountChartProps {
  competitors: RawCompetitorData[];
  yourWordCount?: number;
}

export function WordCountChart({
  competitors,
  yourWordCount,
}: WordCountChartProps) {
  const data = [
    ...(yourWordCount
      ? [
          {
            name: "You",
            words: yourWordCount,
            isYou: true,
          },
        ]
      : []),
    ...competitors.map((comp) => {
      const domain = new URL(comp.url).hostname.replace("www.", "");
      return {
        name: domain.length > 15 ? domain.slice(0, 15) + "..." : domain,
        words: comp.word_count,
        isYou: false,
      };
    }),
  ].sort((a, b) => b.words - a.words);

  const avgWords = Math.round(
    competitors.reduce((sum, c) => sum + c.word_count, 0) / competitors.length
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Word Count Comparison
        </CardTitle>
      </CardHeader>
      <CardContent>
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
                    return (
                      <div className="rounded-lg border bg-background px-3 py-2 shadow-sm">
                        <p className="text-sm font-medium">
                          {payload[0].payload.name}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {(payload[0].value as number).toLocaleString()} words
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
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
              <Bar dataKey="words" radius={[0, 4, 4, 0]} barSize={24}>
                {data.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={
                      entry.isYou
                        ? "#2bbaa0"
                        : "rgba(148, 163, 184, 0.3)"
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
