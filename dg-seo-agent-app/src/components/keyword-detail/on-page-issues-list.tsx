import { AlertTriangle, AlertCircle, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface OnPageIssuesListProps {
  issues: string[];
}

function getIssueSeverity(issue: string): "high" | "medium" | "low" {
  const lower = issue.toLowerCase();
  if (
    lower.includes("missing") ||
    lower.includes("no h1") ||
    lower.includes("no page exists") ||
    lower.includes("not found")
  )
    return "high";
  if (
    lower.includes("too") ||
    lower.includes("only") ||
    lower.includes("below") ||
    lower.includes("multiple")
  )
    return "medium";
  return "low";
}

const severityConfig = {
  high: {
    icon: AlertCircle,
    color: "text-red-600 dark:text-red-400",
    bg: "bg-red-50 dark:bg-red-950",
  },
  medium: {
    icon: AlertTriangle,
    color: "text-amber-600 dark:text-amber-400",
    bg: "bg-amber-50 dark:bg-amber-950",
  },
  low: {
    icon: Info,
    color: "text-teal-600 dark:text-teal-400",
    bg: "bg-teal-50 dark:bg-teal-950",
  },
};

export function OnPageIssuesList({ issues }: OnPageIssuesListProps) {
  if (issues.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">On-Page Issues</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-emerald-600 dark:text-emerald-400">
            No on-page issues detected
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          On-Page Issues ({issues.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {issues.map((issue, i) => {
          const severity = getIssueSeverity(issue);
          const config = severityConfig[severity];
          const Icon = config.icon;
          return (
            <div
              key={i}
              className={`flex items-start gap-3 rounded-lg p-3 ${config.bg}`}
            >
              <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${config.color}`} />
              <p className="text-sm">{issue}</p>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
