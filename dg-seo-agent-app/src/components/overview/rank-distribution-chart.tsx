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
} from "recharts";
import type { KeywordData } from "@/lib/types";

interface RankDistributionChartProps {
  keywords: KeywordData[];
}

export function RankDistributionChart({
  keywords,
}: RankDistributionChartProps) {
  const buckets = [
    { label: "1-3", min: 1, max: 3, color: "hsl(142, 76%, 36%)" },
    { label: "4-10", min: 4, max: 10, color: "hsl(142, 60%, 50%)" },
    { label: "11-20", min: 11, max: 20, color: "hsl(38, 92%, 50%)" },
    { label: "21-50", min: 21, max: 50, color: "hsl(25, 95%, 53%)" },
    { label: "50+", min: 51, max: 100, color: "hsl(0, 72%, 51%)" },
    { label: "N/R", min: -1, max: -1, color: "#94a3b8" },
  ];

  const data = buckets.map((bucket) => ({
    name: bucket.label,
    count:
      bucket.min === -1
        ? keywords.filter((kw) => kw.your_rank === null).length
        : keywords.filter(
            (kw) =>
              kw.your_rank !== null &&
              kw.your_rank >= bucket.min &&
              kw.your_rank <= bucket.max
          ).length,
    color: bucket.color,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Rank Distribution
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Where each of your {keywords.length} keyword
          {keywords.length === 1 ? "" : "s"} currently rank{keywords.length === 1 ? "s" : ""} on Google
        </p>
      </CardHeader>
      <CardContent>
        <div className="h-[200px] w-full">
          <ResponsiveContainer width="100%" height={200} minWidth={200}>
            <BarChart data={data}>
              <XAxis
                dataKey="name"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                fontSize={12}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="rounded-lg border bg-background p-2 shadow-sm">
                        <p className="text-sm font-medium">
                          Position {payload[0].payload.name}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {payload[0].value} keyword
                          {(payload[0].value as number) !== 1 ? "s" : ""}
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {data.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
