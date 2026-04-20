import { Card, CardContent } from "@/components/ui/card";
import type { PageSpeed, WebVitalRating } from "@/lib/types";

interface CoreWebVitalsProps {
  pageSpeed: PageSpeed;
}

const vitals = [
  {
    key: "lcp" as const,
    label: "LCP",
    unit: "s",
    description: "Largest Contentful Paint",
    thresholds: { good: 2.5, poor: 4.0 },
  },
  {
    key: "fcp" as const,
    label: "FCP",
    unit: "s",
    description: "First Contentful Paint",
    thresholds: { good: 1.8, poor: 3.0 },
  },
  {
    key: "cls" as const,
    label: "CLS",
    unit: "",
    description: "Cumulative Layout Shift",
    thresholds: { good: 0.1, poor: 0.25 },
  },
  {
    key: "inp" as const,
    label: "INP",
    unit: "ms",
    description: "Interaction to Next Paint",
    thresholds: { good: 200, poor: 500 },
  },
  {
    key: "ttfb" as const,
    label: "TTFB",
    unit: "s",
    description: "Time to First Byte",
    thresholds: { good: 0.8, poor: 1.8 },
  },
];

const ratingStyles: Record<
  WebVitalRating,
  { dot: string; bg: string; text: string; bar: string }
> = {
  FAST: {
    dot: "bg-emerald-500",
    bg: "bg-emerald-50 dark:bg-emerald-950/40",
    text: "text-emerald-700 dark:text-emerald-400",
    bar: "bg-emerald-500",
  },
  AVERAGE: {
    dot: "bg-amber-500",
    bg: "bg-amber-50 dark:bg-amber-950/40",
    text: "text-amber-700 dark:text-amber-400",
    bar: "bg-amber-500",
  },
  SLOW: {
    dot: "bg-red-500",
    bg: "bg-red-50 dark:bg-red-950/40",
    text: "text-red-700 dark:text-red-400",
    bar: "bg-red-500",
  },
};

export function CoreWebVitals({ pageSpeed }: CoreWebVitalsProps) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {vitals.map((vital) => {
        const value = pageSpeed[vital.key];
        const ratingKey = `${vital.key}_rating` as keyof PageSpeed;
        const rating = pageSpeed[ratingKey] as WebVitalRating;
        const style = ratingStyles[rating];

        // Calculate bar percentage based on thresholds
        const maxVal = vital.thresholds.poor * 1.5;
        const barPercent = Math.min((Number(value) / maxVal) * 100, 100);

        return (
          <Card key={vital.key} className={`${style.bg} border-0`}>
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    {vital.label}
                  </span>
                  <div className="flex items-center gap-1">
                    <div className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
                    <span className={`text-[10px] font-semibold ${style.text}`}>
                      {rating}
                    </span>
                  </div>
                </div>
              </div>
              <p className={`text-2xl font-bold tabular-nums ${style.text}`}>
                {value}
                {vital.unit && (
                  <span className="ml-0.5 text-sm font-medium opacity-70">
                    {vital.unit}
                  </span>
                )}
              </p>
              <p className="mt-1 text-[11px] text-muted-foreground">
                {vital.description}
              </p>
              {/* Mini progress bar */}
              <div className="mt-2 h-1 w-full rounded-full bg-muted">
                <div
                  className={`h-full rounded-full ${style.bar} transition-all`}
                  style={{ width: `${barPercent}%` }}
                />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
