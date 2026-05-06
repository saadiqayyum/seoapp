import Link from "next/link";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ArrowRight, AlertCircle } from "lucide-react";
import { computeActionItems } from "@/lib/computations";
import type { KeywordData } from "@/lib/types";

interface ActionPrioritiesCardProps {
  keywords: KeywordData[];
}

export function ActionPrioritiesCard({ keywords }: ActionPrioritiesCardProps) {
  const items = computeActionItems(keywords);
  const counts = {
    high: items.filter((i) => i.priority === "high").length,
    medium: items.filter((i) => i.priority === "medium").length,
    low: items.filter((i) => i.priority === "low").length,
  };
  const total = counts.high + counts.medium + counts.low;

  return (
    <Card className="flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <AlertCircle className="h-4 w-4" />
          Action Priorities
        </CardTitle>
        <Link
          href="/actions"
          className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
        >
          View all <ArrowRight className="h-3 w-3" />
        </Link>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col justify-center gap-4">
        <div>
          <p className="text-3xl font-bold tracking-tight tabular-nums">
            {total}
          </p>
          <p className="text-xs text-muted-foreground">
            Open recommendations across all keywords
          </p>
        </div>

        <div className="space-y-2">
          <PriorityRow
            label="High priority"
            count={counts.high}
            total={total}
            barClass="bg-red-500 dark:bg-red-400"
            textClass="text-red-700 dark:text-red-400"
          />
          <PriorityRow
            label="Medium priority"
            count={counts.medium}
            total={total}
            barClass="bg-amber-500 dark:bg-amber-400"
            textClass="text-amber-700 dark:text-amber-400"
          />
          <PriorityRow
            label="Low priority"
            count={counts.low}
            total={total}
            barClass="bg-muted-foreground/40"
            textClass="text-muted-foreground"
          />
        </div>
      </CardContent>
    </Card>
  );
}

function PriorityRow({
  label,
  count,
  total,
  barClass,
  textClass,
}: {
  label: string;
  count: number;
  total: number;
  barClass: string;
  textClass: string;
}) {
  const pct = total === 0 ? 0 : (count / total) * 100;
  return (
    <div className="space-y-1">
      <div className="flex items-baseline justify-between text-xs">
        <span className={`font-medium ${textClass}`}>{label}</span>
        <span className="tabular-nums text-muted-foreground">{count}</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full rounded-full transition-all ${barClass}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
