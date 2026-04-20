"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RadialBarChart, RadialBar, PolarAngleAxis } from "recharts";

interface PageSpeedScoreProps {
  score: number;
}

export function PageSpeedScore({ score }: PageSpeedScoreProps) {
  const color =
    score >= 90
      ? "hsl(142, 76%, 36%)"
      : score >= 50
        ? "hsl(38, 92%, 50%)"
        : "hsl(0, 72%, 51%)";

  const data = [{ value: score, fill: color }];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Performance Score
        </CardTitle>
      </CardHeader>
      <CardContent className="flex items-center justify-center">
        <div className="relative h-[180px] w-[180px]">
          <RadialBarChart
            width={180}
            height={180}
            cx="50%"
            cy="50%"
            innerRadius="70%"
            outerRadius="100%"
            barSize={12}
            data={data}
            startAngle={90}
            endAngle={-270}
          >
            <PolarAngleAxis
              type="number"
              domain={[0, 100]}
              angleAxisId={0}
              tick={false}
            />
            <RadialBar
              background={{ fill: "#e8edf2" }}
              dataKey="value"
              cornerRadius={8}
              angleAxisId={0}
            />
          </RadialBarChart>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold" style={{ color }}>
              {score}
            </span>
            <span className="text-xs text-muted-foreground">/ 100</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
