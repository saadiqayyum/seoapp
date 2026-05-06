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

interface SerpFeaturesSummaryProps {
  data: { feature: string; count: number }[];
  totalKeywords: number;
}

export function SerpFeaturesSummary({
  data,
  totalKeywords,
}: SerpFeaturesSummaryProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          SERP Features Detected
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Special Google result types appearing for your {totalKeywords} keyword
          {totalKeywords === 1 ? "" : "s"}
        </p>
      </CardHeader>
      <CardContent>
        <div className="h-[200px] w-full">
          <ResponsiveContainer width="100%" height={200} minWidth={200}>
            <BarChart data={data} layout="vertical">
              <XAxis
                type="number"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <YAxis
                type="category"
                dataKey="feature"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                width={110}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="rounded-lg border bg-background p-2 shadow-sm">
                        <p className="text-sm font-medium">
                          {payload[0].payload.feature}
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
              <Bar
                dataKey="count"
                fill="#2bbaa0"
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
