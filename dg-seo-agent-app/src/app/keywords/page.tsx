import Link from "next/link";
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
import { Progress } from "@/components/ui/progress";
import { ArrowUpRight, Minus } from "lucide-react";
import { getSignedInUserState } from "@/lib/data";
import { getAggregatedKeywordsForDomain } from "@/lib/audits";
import { EmptyState } from "@/components/layout/empty-state";
import { getRankColor, getSpeedColor } from "@/lib/constants";

export default async function KeywordsPage() {
  const state = await getSignedInUserState();
  if (state.state === "no-domain") return <EmptyState state="no-domain" />;
  if (state.state === "no-audit")
    return <EmptyState state="no-audit" domainLabel={state.domain.label} />;
  if (state.state === "unauthenticated") return null;

  const { domain, user } = state.ctx;
  const keywords = await getAggregatedKeywordsForDomain(user.userId, domain.id);

  return (
    <>
      <Header
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "Keywords" },
        ]}
      />
      <div className="flex-1 space-y-6 p-4 md:p-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Keywords</h2>
          <p className="text-muted-foreground">
            {keywords.length} keywords tracked for{" "}
            <span className="font-medium text-foreground">{domain.label}</span>
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">All Keywords</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Keyword</TableHead>
                    <TableHead className="text-center">Rank</TableHead>
                    <TableHead className="text-center">Page</TableHead>
                    <TableHead className="text-center">Speed</TableHead>
                    <TableHead className="text-center">Int. Links</TableHead>
                    <TableHead className="text-center">Issues</TableHead>
                    <TableHead className="text-center">Gaps</TableHead>
                    <TableHead className="text-center">Backlinks</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {keywords.map((kw) => (
                    <TableRow key={kw.keyword}>
                      <TableCell>
                        <Link
                          href={`/keywords/${encodeURIComponent(kw.keyword)}`}
                          className="group inline-flex items-center gap-1.5 font-medium hover:text-primary transition-colors"
                        >
                          {kw.keyword}
                          <ArrowUpRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </Link>
                        {kw.your_url && (
                          <p className="mt-0.5 max-w-[250px] truncate text-xs text-muted-foreground">
                            {kw.your_url}
                          </p>
                        )}
                      </TableCell>
                      <TableCell className="text-center">
                        <span
                          className={`font-bold tabular-nums ${getRankColor(kw.your_rank)}`}
                        >
                          {kw.your_rank !== null ? `#${kw.your_rank}` : (
                            <Minus className="mx-auto h-4 w-4 text-muted-foreground" />
                          )}
                        </span>
                      </TableCell>
                      <TableCell className="text-center">
                        {kw.your_page !== null ? (
                          <Badge
                            variant={
                              kw.your_page === 1 ? "default" : "secondary"
                            }
                            className="tabular-nums"
                          >
                            P{kw.your_page}
                          </Badge>
                        ) : (
                          <Badge variant="outline">N/R</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-center">
                        {kw.page_speed ? (
                          <div className="flex flex-col items-center gap-1">
                            <span
                              className={`text-sm font-bold tabular-nums ${getSpeedColor(kw.page_speed.score)}`}
                            >
                              {kw.page_speed.score}
                            </span>
                            <Progress
                              value={kw.page_speed.score}
                              className="h-1 w-12"
                            />
                          </div>
                        ) : (
                          <Minus className="mx-auto h-4 w-4 text-muted-foreground" />
                        )}
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex flex-col items-center gap-1">
                          <span className="text-sm tabular-nums text-muted-foreground">
                            {Math.round(kw.internal_link_score * 100)}%
                          </span>
                          <Progress
                            value={kw.internal_link_score * 100}
                            className="h-1 w-12"
                          />
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge
                          variant={
                            kw.on_page_issues.length > 3
                              ? "destructive"
                              : kw.on_page_issues.length > 0
                                ? "secondary"
                                : "outline"
                          }
                          className="tabular-nums"
                        >
                          {kw.on_page_issues.length}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center tabular-nums text-sm">
                        {kw.missing_topics.length}
                      </TableCell>
                      <TableCell className="text-center tabular-nums text-sm">
                        {kw.backlink_gap.length}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
