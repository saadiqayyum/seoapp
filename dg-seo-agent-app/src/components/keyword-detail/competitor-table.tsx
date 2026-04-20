import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { Competitor, RawCompetitorData } from "@/lib/types";

interface CompetitorTableProps {
  competitors: Competitor[];
  rawData: RawCompetitorData[];
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
          <TableHead>Domain</TableHead>
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
                <Badge
                  variant={comp.rank <= 3 ? "default" : "secondary"}
                >
                  #{comp.rank}
                </Badge>
              </TableCell>
              <TableCell className="font-medium">{comp.domain}</TableCell>
              <TableCell className="max-w-[250px] truncate text-sm text-muted-foreground">
                {comp.title}
              </TableCell>
              <TableCell className="text-center">
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
              <TableCell className="text-center">
                {raw?.internal_links ?? "-"}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
