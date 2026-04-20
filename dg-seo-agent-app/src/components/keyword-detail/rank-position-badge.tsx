import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface RankPositionBadgeProps {
  rank: number | null;
  page: number | null;
}

export function RankPositionBadge({ rank, page }: RankPositionBadgeProps) {
  const isGood = rank !== null && rank <= 10;
  const isOk = rank !== null && rank <= 30;

  const bgColor = isGood
    ? "from-emerald-500 to-emerald-600"
    : isOk
      ? "from-amber-500 to-amber-600"
      : rank !== null
        ? "from-red-500 to-red-600"
        : "from-slate-400 to-slate-500";

  return (
    <div className="flex items-center gap-3">
      <div
        className={`flex h-16 w-20 flex-col items-center justify-center rounded-xl bg-gradient-to-br ${bgColor} text-white shadow-sm`}
      >
        <span className="text-2xl font-bold leading-none">
          {rank !== null ? `#${rank}` : "N/R"}
        </span>
        {rank !== null && (
          <span className="mt-0.5 text-[10px] font-medium opacity-80">
            Page {page}
          </span>
        )}
      </div>
      <div className="space-y-0.5">
        {isGood ? (
          <div className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
            <TrendingUp className="h-3.5 w-3.5" />
            <span className="text-xs font-semibold">On Page 1</span>
          </div>
        ) : rank !== null ? (
          <div className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
            <TrendingDown className="h-3.5 w-3.5" />
            <span className="text-xs font-semibold">
              {11 - (rank > 10 ? rank % 10 || 10 : rank)} from page{" "}
              {(page ?? 1) - 1 || 1}
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-1 text-muted-foreground">
            <Minus className="h-3.5 w-3.5" />
            <span className="text-xs font-semibold">Not ranking</span>
          </div>
        )}
        <p className="text-[10px] text-muted-foreground">
          {rank !== null
            ? `Position ${rank} of top 100`
            : "Not found in top 100 results"}
        </p>
      </div>
    </div>
  );
}
