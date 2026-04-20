"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PlayCircle, AlertCircle } from "lucide-react";
import type { DomainSummary } from "@/lib/domains";

export default function NewAuditPage() {
  const router = useRouter();
  const [domains, setDomains] = useState<DomainSummary[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [keywordsText, setKeywordsText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch("/api/domains").then((r) => r.json()),
      fetch("/api/session").then((r) => r.json()),
    ]).then(([d, s]) => {
      setDomains(d.domains ?? []);
      setCurrentId(s.currentDomainId ?? null);
    });
  }, []);

  const current = domains.find((d) => d.id === currentId) ?? null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!currentId) return;

    const keywords = keywordsText
      .split(/[\n,]+/)
      .map((k) => k.trim())
      .filter((k) => k.length > 0);
    if (keywords.length === 0) {
      setError("Add at least one keyword");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch("/api/audits", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domainId: currentId, keywords }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Failed to start audit");
        return;
      }
      router.push(`/audits/${data.audit.id}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex-1 space-y-6 p-6 md:p-8">
      <header>
        <h1 className="text-xl font-bold tracking-tight">New Audit</h1>
        <p className="text-sm text-muted-foreground">
          Run the agent against your current domain.
        </p>
      </header>

      {!current ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <AlertCircle className="h-10 w-10 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">
              You don&apos;t have an active domain yet.
            </p>
            <Button render={<Link href="/domains">Add a domain</Link>} />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-sm font-medium">
              <span className="flex items-center gap-2">
                <PlayCircle className="h-4 w-4" />
                Run audit
              </span>
              <Badge variant="secondary">{current.label}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label
                  htmlFor="keywords"
                  className="text-xs font-medium text-muted-foreground"
                >
                  Keywords (one per line or comma-separated)
                </label>
                <textarea
                  id="keywords"
                  value={keywordsText}
                  onChange={(e) => setKeywordsText(e.target.value)}
                  rows={6}
                  className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  placeholder="seo audit tool&#10;keyword research&#10;backlink checker"
                  required
                />
                <p className="text-[11px] text-muted-foreground">
                  Target: <span className="font-mono">{current.url}</span>
                </p>
              </div>
              {error && (
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              )}
              <Button type="submit" disabled={submitting}>
                {submitting ? "Starting..." : "Start audit"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

