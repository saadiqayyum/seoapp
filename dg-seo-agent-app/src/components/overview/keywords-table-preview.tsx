import Link from "next/link";
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
import { ArrowRight, ArrowUpRight, Minus } from "lucide-react";
import type { KeywordData } from "@/lib/types";
import { getRankColor, getSpeedColor } from "@/lib/constants";

interface KeywordsTablePreviewProps {
  keywords: KeywordData[];
}

export function KeywordsTablePreview({ keywords }: KeywordsTablePreviewProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium">Keywords Overview</CardTitle>
        <Link
          href="/keywords"
          className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
        >
          View details <ArrowRight className="h-3 w-3" />
        </Link>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Keyword</TableHead>
              <TableHead className="text-center">Rank</TableHead>
              <TableHead className="text-center">Page</TableHead>
              <TableHead className="text-center">Speed</TableHead>
              <TableHead className="text-center">Links</TableHead>
              <TableHead className="text-center">Issues</TableHead>
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
                </TableCell>
                <TableCell className="text-center">
                  <span
                    className={`inline-flex h-8 w-12 items-center justify-center rounded-md text-sm font-bold ${getRankColor(kw.your_rank)}`}
                  >
                    {kw.your_rank !== null ? `#${kw.your_rank}` : (
                      <Minus className="h-4 w-4 text-muted-foreground" />
                    )}
                  </span>
                </TableCell>
                <TableCell className="text-center">
                  {kw.your_page !== null ? (
                    <Badge
                      variant={kw.your_page === 1 ? "default" : "secondary"}
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
                        className="h-1 w-10"
                      />
                    </div>
                  ) : (
                    <Minus className="mx-auto h-4 w-4 text-muted-foreground" />
                  )}
                </TableCell>
                <TableCell className="text-center">
                  <div className="flex flex-col items-center gap-1">
                    <span className="text-xs tabular-nums text-muted-foreground">
                      {Math.round(kw.internal_link_score * 100)}%
                    </span>
                    <Progress
                      value={kw.internal_link_score * 100}
                      className="h-1 w-10"
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
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
