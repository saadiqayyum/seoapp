"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Globe, Plus, Trash2, Check } from "lucide-react";
import type { DomainSummary } from "@/lib/domains";

export default function DomainsPage() {
  const router = useRouter();
  const [domains, setDomains] = useState<DomainSummary[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [url, setUrl] = useState("");
  const [label, setLabel] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    const [domainsRes, meRes] = await Promise.all([
      fetch("/api/domains"),
      fetch("/api/session"),
    ]);
    const domainsData = await domainsRes.json();
    const meData = await meRes.json().catch(() => ({}));
    setDomains(domainsData.domains ?? []);
    setCurrentId(meData.currentDomainId ?? null);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch("/api/domains", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, label: label || undefined }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "Failed to add domain");
        return;
      }
      setUrl("");
      setLabel("");
      await load();
      router.refresh();
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this domain? Audits will be kept but hidden.")) return;
    await fetch(`/api/domains/${id}`, { method: "DELETE" });
    await load();
    router.refresh();
  }

  async function handleSelect(id: string) {
    await fetch("/api/session/current-domain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ domainId: id }),
    });
    setCurrentId(id);
    router.refresh();
  }

  return (
    <div className="flex-1 space-y-6 p-6 md:p-8">
      <header>
        <h1 className="text-xl font-bold tracking-tight">Domains</h1>
        <p className="text-sm text-muted-foreground">
          Add the sites you want to audit. Switch between them from the
          sidebar.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <Plus className="h-4 w-4" />
            Add a domain
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAdd} className="grid gap-3 md:grid-cols-[2fr_1fr_auto]">
            <Input
              type="text"
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
            <Input
              type="text"
              placeholder="Label (optional)"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
            />
            <Button type="submit" disabled={submitting}>
              {submitting ? "Adding..." : "Add"}
            </Button>
          </form>
          {error && (
            <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <Globe className="h-4 w-4" />
            Your domains
            <Badge variant="secondary">{domains.length}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : domains.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No domains yet. Add your first above.
            </p>
          ) : (
            <ul className="space-y-2">
              {domains.map((d) => {
                const isCurrent = d.id === currentId;
                return (
                  <li
                    key={d.id}
                    className="flex items-center justify-between rounded-lg border bg-card/50 px-4 py-3"
                  >
                    <div className="min-w-0">
                      <p className="flex items-center gap-2 text-sm font-medium">
                        {d.label}
                        {isCurrent && (
                          <Badge
                            variant="secondary"
                            className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300"
                          >
                            <Check className="mr-1 h-3 w-3" />
                            Current
                          </Badge>
                        )}
                      </p>
                      <p className="truncate text-xs text-muted-foreground">
                        {d.url}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      {!isCurrent && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSelect(d.id)}
                        >
                          Set current
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(d.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
