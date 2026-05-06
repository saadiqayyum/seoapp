import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ExternalLink } from "lucide-react";
import type { Competitor, RawCompetitorData } from "@/lib/types";

interface CompetitorTableProps {
  competitors: Competitor[];
  rawData: RawCompetitorData[];
}

function pathOf(url: string): string {
  try {
    const u = new URL(url);
    return `${u.pathname}${u.search}` || "/";
  } catch {
    return url;
  }
}

export function CompetitorTable({
  competitors,
  rawData,
}: CompetitorTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Rank</TableHead>
          <TableHead>Page</TableHead>
          <TableHead>Title</TableHead>
          <TableHead className="text-center">Words</TableHead>
          <TableHead className="text-center">Schema</TableHead>
          <TableHead className="text-center">Int. Links</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {competitors.map((comp) => {
          const raw = rawData.find((r) => r.url === comp.url);
          return (
            <TableRow key={comp.url}>
              <TableCell>
                <Badge variant={comp.rank <= 3 ? "default" : "secondary"}>
                  #{comp.rank}
                </Badge>
              </TableCell>
              <TableCell className="max-w-[340px]">
                <a
                  href={comp.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group inline-flex max-w-full flex-col gap-0.5"
                  title={comp.url}
                >
                  <span className="inline-flex items-center gap-1.5 font-medium transition-colors group-hover:text-primary">
                    <span className="truncate">{comp.domain}</span>
                    <ExternalLink className="h-3 w-3 flex-shrink-0 opacity-0 transition-opacity group-hover:opacity-100" />
                  </span>
                  <span className="truncate text-xs text-muted-foreground transition-colors group-hover:text-primary/70">
                    {pathOf(comp.url)}
                  </span>
                </a>
              </TableCell>
              <TableCell className="max-w-[250px] truncate text-sm text-muted-foreground">
                {comp.title}
              </TableCell>
              <TableCell className="text-center tabular-nums">
                {raw?.word_count?.toLocaleString() ?? "-"}
              </TableCell>
              <TableCell className="text-center">
                {raw ? (
                  <Badge variant={raw.has_schema ? "default" : "outline"}>
                    {raw.has_schema ? "Yes" : "No"}
                  </Badge>
                ) : (
                  "-"
                )}
              </TableCell>
              <TableCell className="text-center tabular-nums">
                {raw?.internal_links ?? "-"}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
