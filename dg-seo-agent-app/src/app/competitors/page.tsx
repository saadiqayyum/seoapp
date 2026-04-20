import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Users, Trophy, Target } from "lucide-react";
import { getSignedInUserState } from "@/lib/data";
import { EmptyState } from "@/components/layout/empty-state";
import { aggregateCompetitors } from "@/lib/computations";
import { CompetitorFrequencyChart } from "@/components/competitors/competitor-frequency-chart";

export default async function CompetitorsPage() {
  const state = await getSignedInUserState();
  if (state.state === "no-domain") return <EmptyState state="no-domain" />;
  if (state.state === "no-audit")
    return <EmptyState state="no-audit" domainLabel={state.domain.label} />;
  if (state.state === "unauthenticated") return null;

  const { report } = state.ctx;
  const competitors = aggregateCompetitors(report.keywords);
  const multiKeywordCompetitors = competitors.filter((c) => c.count >= 2);

  return (
    <>
      <Header
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "Competitors" },
        ]}
      />
      <div className="flex-1 space-y-6 p-4 md:p-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            Competitor Analysis
          </h2>
          <p className="text-muted-foreground">
            Cross-keyword competitor intelligence
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <Card className="relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-teal-500/10 to-emerald-500/10 pointer-events-none" />
            <CardContent className="relative pt-5">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-100 dark:bg-teal-900/50">
                  <Users className="h-5 w-5 text-teal-600 dark:text-teal-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{competitors.length}</p>
                  <p className="text-xs text-muted-foreground">
                    Total Competitor Domains
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-amber-500/10 to-orange-500/10 pointer-events-none" />
            <CardContent className="relative pt-5">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-100 dark:bg-amber-900/50">
                  <Trophy className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold">
                    {multiKeywordCompetitors.length}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Multi-Keyword Competitors
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 pointer-events-none" />
            <CardContent className="relative pt-5">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-100 dark:bg-emerald-900/50">
                  <Target className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold">
                    #{competitors[0]?.avgRank ?? "-"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Top Competitor Avg. Rank
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <CompetitorFrequencyChart data={competitors} />

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              All Competitor Domains
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-8">#</TableHead>
                  <TableHead>Domain</TableHead>
                  <TableHead className="text-center">
                    Keywords Competing
                  </TableHead>
                  <TableHead className="text-center">Avg. Rank</TableHead>
                  <TableHead>Competing For</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {competitors.map((comp, i) => (
                  <TableRow key={comp.domain}>
                    <TableCell className="text-muted-foreground text-xs font-medium">
                      {i + 1}
                    </TableCell>
                    <TableCell className="font-medium">{comp.domain}</TableCell>
                    <TableCell className="text-center">
                      <Badge
                        variant={
                          comp.count >= 3
                            ? "default"
                            : comp.count >= 2
                              ? "secondary"
                              : "outline"
                        }
                      >
                        {comp.count}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="font-semibold tabular-nums">
                        #{comp.avgRank}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {comp.keywords.map((kw) => (
                          <Badge
                            key={kw}
                            variant="outline"
                            className="text-[10px] font-normal"
                          >
                            {kw}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
