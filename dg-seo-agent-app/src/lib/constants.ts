export const RATING_COLORS = {
  FAST: "text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950",
  AVERAGE:
    "text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-950",
  SLOW: "text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-950",
} as const;

export const RANK_THRESHOLDS = {
  GOOD: 10,
  AVERAGE: 30,
} as const;

export function getRankColor(rank: number | null): string {
  if (rank === null) return "text-muted-foreground";
  if (rank <= RANK_THRESHOLDS.GOOD)
    return "text-emerald-600 dark:text-emerald-400";
  if (rank <= RANK_THRESHOLDS.AVERAGE)
    return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

export function getSpeedColor(score: number): string {
  if (score >= 90) return "text-emerald-600 dark:text-emerald-400";
  if (score >= 50) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

export function getScoreColor(score: number): string {
  if (score >= 0.7) return "text-emerald-600 dark:text-emerald-400";
  if (score >= 0.4) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

export const CATEGORY_LABELS: Record<string, string> = {
  "on-page": "On-Page",
  content: "Content",
  backlinks: "Backlinks",
  "internal-links": "Internal Links",
  speed: "Speed",
  serp: "SERP",
  competitor: "Competitor",
} as const;

export const CATEGORY_COLORS: Record<string, string> = {
  "on-page": "bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-300",
  content:
    "bg-sky-100 text-sky-800 dark:bg-sky-900 dark:text-sky-300",
  backlinks:
    "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300",
  "internal-links":
    "bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-300",
  speed:
    "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300",
  serp: "bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-300",
  competitor:
    "bg-violet-100 text-violet-800 dark:bg-violet-900 dark:text-violet-300",
} as const;

export const INSIGHT_CATEGORY_LABELS: Record<string, string> = {
  word_count: "Content Depth",
  schema: "Schema Markup",
  headings: "Heading Structure",
  meta: "Meta Description",
  internal_links: "Internal Links",
  external_links: "Outbound Citations",
  title: "Title Tag",
} as const;

export const PRIORITY_COLORS: Record<string, string> = {
  high: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
  medium:
    "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300",
  low: "bg-slate-100 text-slate-800 dark:bg-slate-900 dark:text-slate-300",
} as const;
