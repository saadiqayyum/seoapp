import { Header } from "@/components/layout/header";
import { Card, CardContent } from "@/components/ui/card";
import { getSignedInUserState } from "@/lib/data";
import { getAggregatedKeywordsForDomain } from "@/lib/audits";
import { EmptyState } from "@/components/layout/empty-state";
import { computeActionItems } from "@/lib/computations";
import { ActionItemsList } from "@/components/actions/action-items-list";
import { AlertCircle, AlertTriangle, Info } from "lucide-react";

export default async function ActionsPage() {
  const state = await getSignedInUserState();
  if (state.state === "no-domain") return <EmptyState state="no-domain" />;
  if (state.state === "no-audit")
    return <EmptyState state="no-audit" domainLabel={state.domain.label} />;
  if (state.state === "unauthenticated") return null;

  const { domain, user } = state.ctx;
  const keywords = await getAggregatedKeywordsForDomain(user.userId, domain.id);
  const actionItems = computeActionItems(keywords);

  const highCount = actionItems.filter((i) => i.priority === "high").length;
  const medCount = actionItems.filter((i) => i.priority === "medium").length;
  const lowCount = actionItems.filter((i) => i.priority === "low").length;

  return (
    <>
      <Header
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "Action Items" },
        ]}
      />
      <div className="flex-1 space-y-6 p-4 md:p-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Action Items</h2>
          <p className="text-muted-foreground">
            Prioritized improvements across all keywords
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <Card className="border-red-200 dark:border-red-900">
            <CardContent className="flex items-center gap-3 pt-5">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-100 dark:bg-red-900/50">
                <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <p className="text-xl font-bold text-red-700 dark:text-red-400">
                  {highCount}
                </p>
                <p className="text-xs text-muted-foreground">High Priority</p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-amber-200 dark:border-amber-900">
            <CardContent className="flex items-center gap-3 pt-5">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-100 dark:bg-amber-900/50">
                <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <p className="text-xl font-bold text-amber-700 dark:text-amber-400">
                  {medCount}
                </p>
                <p className="text-xs text-muted-foreground">
                  Medium Priority
                </p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200 dark:border-slate-800">
            <CardContent className="flex items-center gap-3 pt-5">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800">
                <Info className="h-4 w-4 text-slate-600 dark:text-slate-400" />
              </div>
              <div>
                <p className="text-xl font-bold">{lowCount}</p>
                <p className="text-xs text-muted-foreground">Low Priority</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <ActionItemsList items={actionItems} />
      </div>
    </>
  );
}
