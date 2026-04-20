"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { History, PlayCircle, ArrowRight } from "lucide-react";
import type { AuditSummary } from "@/lib/audits";
import type { DomainSummary } from "@/lib/domains";

const STATUS_COLORS: Record<AuditSummary["status"], string> = {
  pending: "bg-slate-100 text-slate-800 dark:bg-slate-900 dark:text-slate-300",
  running: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300",
  complete:
    "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300",
  failed: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
};

export default function AuditsPage() {
  const [audits, setAudits] = useState<AuditSummary[]>([]);
  const [currentDomain, setCurrentDomain] = useState<DomainSummary | null>(
    null,
  );
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const sessionRes = await fetch("/api/session");
      const session = await sessionRes.json();
      if (!session.currentDomainId) {
        setAudits([]);
        setCurrentDomain(null);
        return;
      }
      const [auditsRes, domainsRes] = await Promise.all([
        fetch(`/api/audits?domainId=${session.currentDomainId}`),
        fetch("/api/domains"),
      ]);
      const auditsData = await auditsRes.json();
      const domainsData = await domainsRes.json();
      setAudits(auditsData.audits ?? []);
      setCurrentDomain(
        domainsData.domains?.find(
          (d: DomainSummary) => d.id === session.currentDomainId,
        ) ?? null,
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="flex-1 space-y-6 p-6 md:p-8">
      <header className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Audit History</h1>
          <p className="text-sm text-muted-foreground">
            {currentDomain
              ? `All audits for ${currentDomain.label}`
              : "Select a domain to see its audits"}
          </p>
        </div>
        {currentDomain && (
          <Button
            render={
              <Link href="/audits/new">
                <PlayCircle className="mr-1.5 h-4 w-4" />
                New audit
              </Link>
            }
          />
        )}
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <History className="h-4 w-4" />
            Runs
            <Badge variant="secondary">{audits.length}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : !currentDomain ? (
            <p className="text-sm text-muted-foreground">
              No current domain selected.
            </p>
          ) : audits.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No audits yet. Start your first above.
            </p>
          ) : (
            <ul className="space-y-2">
              {audits.map((a) => (
                <li key={a.id}>
                  <Link
                    href={`/audits/${a.id}`}
                    className="flex items-center justify-between rounded-lg border bg-card/50 px-4 py-3 hover:bg-muted/30"
                  >
                    <div className="min-w-0">
                      <p className="flex items-center gap-2 text-sm font-medium">
                        {a.keywords.slice(0, 3).join(", ")}
                        {a.keywords.length > 3 && (
                          <span className="text-xs text-muted-foreground">
                            +{a.keywords.length - 3}
                          </span>
                        )}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(a.createdAt).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="secondary"
                        className={STATUS_COLORS[a.status]}
                      >
                        {a.status}
                      </Badge>
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
