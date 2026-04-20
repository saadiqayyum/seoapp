"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Check, ChevronsUpDown, Globe, Plus, Settings } from "lucide-react";
import { Popover } from "@base-ui/react";
import type { DomainSummary } from "@/lib/domains";

export function DomainSwitcher() {
  const router = useRouter();
  const [domains, setDomains] = useState<DomainSummary[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  async function load() {
    const [dRes, sRes] = await Promise.all([
      fetch("/api/domains"),
      fetch("/api/session"),
    ]);
    if (!dRes.ok) return;
    const d = await dRes.json();
    const s = await sRes.json();
    setDomains(d.domains ?? []);
    setCurrentId(s.currentDomainId ?? null);
  }

  useEffect(() => {
    load();
  }, []);

  const current = domains.find((d) => d.id === currentId) ?? null;

  async function handleSelect(id: string) {
    await fetch("/api/session/current-domain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ domainId: id }),
    });
    setCurrentId(id);
    setOpen(false);
    router.refresh();
  }

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger
        render={
          <button className="flex w-full items-center gap-2 rounded-lg border border-border/60 bg-card/50 px-2.5 py-2 text-left transition-colors hover:bg-muted">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
              <Globe className="h-3.5 w-3.5" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold">
                {current?.label ?? "No domain"}
              </p>
              <p className="truncate text-[10px] text-muted-foreground">
                {current ? "Active" : "Add one to start"}
              </p>
            </div>
            <ChevronsUpDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          </button>
        }
      />
      <Popover.Portal>
        <Popover.Positioner sideOffset={6} align="start">
          <Popover.Popup className="z-50 w-64 rounded-lg border bg-popover p-2 text-popover-foreground shadow-md">
            <p className="px-2 pb-1.5 pt-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
              Current domain
            </p>
            <ul className="space-y-0.5">
              {domains.length === 0 ? (
                <li className="px-2 py-2 text-xs text-muted-foreground">
                  No domains yet
                </li>
              ) : (
                domains.map((d) => {
                  const isCurrent = d.id === currentId;
                  return (
                    <li key={d.id}>
                      <button
                        type="button"
                        onClick={() => handleSelect(d.id)}
                        className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-muted"
                      >
                        <Globe className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-xs font-medium">
                            {d.label}
                          </p>
                          <p className="truncate text-[10px] text-muted-foreground">
                            {d.url}
                          </p>
                        </div>
                        {isCurrent && (
                          <Check className="h-3.5 w-3.5 shrink-0 text-primary" />
                        )}
                      </button>
                    </li>
                  );
                })
              )}
            </ul>
            <div className="my-1.5 border-t border-border/60" />
            <Link
              href="/domains"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs hover:bg-muted"
            >
              <Settings className="h-3.5 w-3.5" />
              Manage
            </Link>
            <Link
              href="/domains"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs hover:bg-muted"
            >
              <Plus className="h-3.5 w-3.5" />
              Add domain
            </Link>
          </Popover.Popup>
        </Popover.Positioner>
      </Popover.Portal>
    </Popover.Root>
  );
}
