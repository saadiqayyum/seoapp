"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RadialBarChart, RadialBar, PolarAngleAxis } from "recharts";

interface HealthScoreGaugeProps {
  score: number;
}

export function HealthScoreGauge({ score }: HealthScoreGaugeProps) {
  const color =
    score >= 70
      ? "hsl(152, 69%, 41%)"
      : score >= 40
        ? "hsl(38, 92%, 50%)"
        : "hsl(0, 84%, 60%)";

  const label =
    score >= 70 ? "Good" : score >= 40 ? "Needs Work" : "Critical";

  const data = [{ value: score, fill: color }];

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle className="text-sm font-medium">Health Score</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-1 items-center justify-center pb-6">
        <div className="relative h-[200px] w-[200px]">
          <RadialBarChart
            width={200}
            height={200}
            cx="50%"
            cy="50%"
            innerRadius="72%"
            outerRadius="100%"
            barSize={16}
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
              cornerRadius={10}
              angleAxisId={0}
            />
          </RadialBarChart>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-4xl font-bold" style={{ color }}>
              {score}
            </span>
            <span
              className="mt-0.5 text-xs font-semibold uppercase tracking-wider"
              style={{ color }}
            >
              {label}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
