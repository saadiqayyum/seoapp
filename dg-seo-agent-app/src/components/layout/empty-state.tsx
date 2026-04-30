import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Globe, PlayCircle } from "lucide-react";

interface EmptyStateProps {
  state: "no-domain" | "no-audit";
  domainLabel?: string;
}

export function EmptyState({ state, domainLabel }: EmptyStateProps) {
  if (state === "no-domain") {
    return (
      <div className="flex flex-1 items-center justify-center p-6 md:p-8">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <Globe className="h-10 w-10 text-muted-foreground/40" />
            <p className="text-sm font-medium">No domain yet</p>
            <p className="text-xs text-muted-foreground">
              Add a site to start running SEO audits against it.
            </p>
            <Button
              nativeButton={false}
              render={<Link href="/domains">Add a domain</Link>}
            />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-1 items-center justify-center p-6 md:p-8">
      <Card className="w-full max-w-md">
        <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
          <PlayCircle className="h-10 w-10 text-muted-foreground/40" />
          <p className="text-sm font-medium">
            No completed audits for {domainLabel ?? "this domain"}
          </p>
          <p className="text-xs text-muted-foreground">
            Kick off your first run — the agent analyzes rankings, competitors,
            and on-page signals.
          </p>
          <Button
            nativeButton={false}
            render={<Link href="/audits/new">Start audit</Link>}
          />
        </CardContent>
      </Card>
    </div>
  );
}
