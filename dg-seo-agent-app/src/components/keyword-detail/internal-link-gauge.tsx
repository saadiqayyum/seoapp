import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Link2, AlertTriangle } from "lucide-react";

interface InternalLinkGaugeProps {
  score: number;
  issues: string[];
}

export function InternalLinkGauge({ score, issues }: InternalLinkGaugeProps) {
  const percentage = Math.round(score * 100);

  const color =
    score >= 0.7
      ? { stroke: "stroke-emerald-500", text: "text-emerald-600 dark:text-emerald-400", label: "Good" }
      : score >= 0.4
        ? { stroke: "stroke-amber-500", text: "text-amber-600 dark:text-amber-400", label: "Fair" }
        : { stroke: "stroke-red-500", text: "text-red-600 dark:text-red-400", label: "Poor" };

  // SVG circle params
  const size = 100;
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <Link2 className="h-4 w-4" />
          Internal Linking
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-6">
          {/* Circular gauge */}
          <div className="relative shrink-0">
            <svg width={size} height={size} className="-rotate-90">
              <circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                strokeWidth={strokeWidth}
                className="stroke-muted"
              />
              <circle
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                strokeWidth={strokeWidth}
                strokeLinecap="round"
                className={`${color.stroke} transition-all duration-500`}
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={`text-xl font-bold ${color.text}`}>
                {percentage}%
              </span>
              <span className={`text-[10px] font-medium ${color.text}`}>
                {color.label}
              </span>
            </div>
          </div>

          {/* Quick summary */}
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">
              {issues.length === 0
                ? "Internal linking structure looks healthy"
                : `${issues.length} issue${issues.length !== 1 ? "s" : ""} found`}
            </p>
          </div>
        </div>

        {issues.length > 0 && (
          <div className="space-y-2 border-t pt-3">
            {issues.map((issue, i) => (
              <div key={i} className="flex items-start gap-2">
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
                <p className="text-sm text-muted-foreground">{issue}</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
