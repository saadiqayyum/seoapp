"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface CompetitorFrequencyChartProps {
  data: { domain: string; count: number; avgRank: number }[];
}

export function CompetitorFrequencyChart({
  data,
}: CompetitorFrequencyChartProps) {
  const chartData = data.slice(0, 10).map((d) => ({
    name: d.domain.length > 18 ? d.domain.slice(0, 18) + "..." : d.domain,
    fullName: d.domain,
    keywords: d.count,
    avgRank: d.avgRank,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Competitor Frequency Across Keywords
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height={300} minWidth={200}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 10 }}>
              <XAxis
                type="number"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <YAxis
                type="category"
                dataKey="name"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                width={130}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const d = payload[0].payload;
                    return (
                      <div className="rounded-lg border bg-background px-3 py-2 shadow-sm">
                        <p className="text-sm font-medium">{d.fullName}</p>
                        <p className="text-sm text-muted-foreground">
                          Competes on {d.keywords} keyword
                          {d.keywords !== 1 ? "s" : ""}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          Avg. rank: #{d.avgRank}
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Bar
                dataKey="keywords"
                fill="#2bbaa0"
                radius={[0, 6, 6, 0]}
                barSize={20}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
