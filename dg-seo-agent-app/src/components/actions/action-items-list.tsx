"use client";

import { useState } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowUpRight } from "lucide-react";
import type { ActionItem } from "@/lib/types";
import { CATEGORY_LABELS, CATEGORY_COLORS } from "@/lib/constants";

interface ActionItemsListProps {
  items: ActionItem[];
}

const categories = [
  "all",
  "on-page",
  "content",
  "backlinks",
  "internal-links",
  "speed",
  "serp",
] as const;

export function ActionItemsList({ items }: ActionItemsListProps) {
  const [filter, setFilter] = useState<string>("all");

  const filtered =
    filter === "all" ? items : items.filter((i) => i.category === filter);

  const highPriority = filtered.filter((i) => i.priority === "high");
  const mediumPriority = filtered.filter((i) => i.priority === "medium");
  const lowPriority = filtered.filter((i) => i.priority === "low");

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        {categories.map((cat) => {
          const count =
            cat === "all"
              ? items.length
              : items.filter((i) => i.category === cat).length;
          if (cat !== "all" && count === 0) return null;
          return (
            <Button
              key={cat}
              variant={filter === cat ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter(cat)}
              className="h-8 text-xs"
            >
              {cat === "all" ? "All" : CATEGORY_LABELS[cat]}{" "}
              <Badge
                variant={filter === cat ? "secondary" : "outline"}
                className="ml-1.5 h-4 px-1 text-[10px]"
              >
                {count}
              </Badge>
            </Button>
          );
        })}
      </div>

      {highPriority.length > 0 && (
        <PrioritySection label="High Priority" items={highPriority} />
      )}
      {mediumPriority.length > 0 && (
        <PrioritySection label="Medium Priority" items={mediumPriority} />
      )}
      {lowPriority.length > 0 && (
        <PrioritySection label="Low Priority" items={lowPriority} />
      )}

      {filtered.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">
              No action items in this category
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function PrioritySection({
  label,
  items,
}: {
  label: string;
  items: ActionItem[];
}) {
  return (
    <div className="space-y-3">
      <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
        {label} ({items.length})
      </h3>
      <div className="grid gap-3 md:grid-cols-2">
        {items.map((item, i) => (
          <Card key={i} className="group">
            <CardContent className="pt-4 pb-4">
              <div className="space-y-2.5">
                <p className="text-sm font-medium leading-snug">
                  {item.title}
                </p>
                <p className="text-xs leading-relaxed text-muted-foreground">
                  {item.description}
                </p>
                <div className="flex items-center justify-between">
                  <div className="flex flex-wrap gap-1.5">
                    <Badge
                      className={CATEGORY_COLORS[item.category] || ""}
                      variant="secondary"
                    >
                      {CATEGORY_LABELS[item.category]}
                    </Badge>
                  </div>
                  <Link
                    href={`/keywords/${encodeURIComponent(item.keyword)}`}
                    className="inline-flex items-center gap-1 text-xs text-primary opacity-0 group-hover:opacity-100 transition-opacity hover:underline"
                  >
                    {item.keyword}
                    <ArrowUpRight className="h-3 w-3" />
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
