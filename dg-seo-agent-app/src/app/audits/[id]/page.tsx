"use client";

import { useEffect, useState } from "react";
import { use } from "react";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, Loader2, CheckCircle2, ArrowRight } from "lucide-react";
import type { AuditDetail } from "@/lib/audits";

const STATUS_COLORS: Record<AuditDetail["status"], string> = {
  pending: "bg-slate-100 text-slate-800 dark:bg-slate-900 dark:text-slate-300",
  running: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300",
  complete:
    "bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300",
  failed: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
};

export default function AuditDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [audit, setAudit] = useState<AuditDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchOnce(): Promise<AuditDetail["status"] | null> {
      const res = await fetch(`/api/audits/${id}`);
      if (!res.ok) {
        if (!cancelled) {
          const data = await res.json().catch(() => ({}));
          setError(data.error || "Failed to load audit");
        }
        return null;
      }
      const data = await res.json();
      if (cancelled) return null;
      setAudit(data.audit);
      return data.audit.status as AuditDetail["status"];
    }

    async function poll() {
      const status = await fetchOnce();
      if (!status) return;
      if (status === "pending" || status === "running") {
        setTimeout(poll, 3000);
      }
    }

    poll();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (error) {
    return (
      <div className="flex-1 p-6 md:p-8">
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <AlertCircle className="h-10 w-10 text-red-500/70" />
            <p className="text-sm">{error}</p>
            <Button
              nativeButton={false}
              render={<Link href="/audits">Back to history</Link>}
            />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!audit) {
    return (
      <div className="flex-1 p-6 md:p-8">
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    );
  }

  const isTerminal = audit.status === "complete" || audit.status === "failed";

  return (
    <div className="flex-1 space-y-6 p-6 md:p-8">
      <header className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Audit</h1>
          <p className="text-sm text-muted-foreground">
            Started {new Date(audit.createdAt).toLocaleString()}
          </p>
        </div>
        <Badge
          variant="secondary"
          className={STATUS_COLORS[audit.status]}
        >
          {audit.status}
        </Badge>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Keywords</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-1.5">
            {audit.keywords.map((k) => (
              <Badge key={k} variant="outline">
                {k}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {!isTerminal && (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <Loader2 className="h-10 w-10 animate-spin text-primary" />
            <p className="text-sm font-medium">
              Agent is running — this may take a few minutes
            </p>
            <p className="text-xs text-muted-foreground">
              We&apos;ll refresh this page automatically when it&apos;s done.
            </p>
          </CardContent>
        </Card>
      )}

      {audit.status === "failed" && (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <AlertCircle className="h-10 w-10 text-red-500/70" />
            <p className="text-sm font-medium">Agent run failed</p>
            {audit.error && (
              <p className="rounded-md bg-red-50 px-3 py-2 font-mono text-xs text-red-700 dark:bg-red-950/40 dark:text-red-400">
                {audit.error}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {audit.status === "complete" && audit.report && (
        <Card>
          <CardContent className="flex items-center justify-between py-6">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-5 w-5 text-emerald-600" />
              <div>
                <p className="text-sm font-medium">Audit complete</p>
                <p className="text-xs text-muted-foreground">
                  {(audit.report.keywords ?? []).length} keywords analyzed
                </p>
              </div>
            </div>
            <Button
              render={
                <Link href="/">
                  View dashboard
                  <ArrowRight className="ml-1.5 h-4 w-4" />
                </Link>
              }
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
