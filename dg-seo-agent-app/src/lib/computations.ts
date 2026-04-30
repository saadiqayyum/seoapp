import type {
  KeywordData,
  ActionItem,
  MissingTopic,
  CompetitorInsight,
} from "./types";

export function computeHealthScore(keywords: KeywordData[]): number {
  if (!keywords?.length) return 0;

  let totalScore = 0;

  for (const kw of keywords) {
    let kwScore = 0;

    if (kw.your_rank !== null) {
      if (kw.your_rank <= 3) kwScore += 40;
      else if (kw.your_rank <= 10) kwScore += 30;
      else if (kw.your_rank <= 20) kwScore += 20;
      else if (kw.your_rank <= 50) kwScore += 10;
    }

    if (kw.page_speed) {
      kwScore += (kw.page_speed.score / 100) * 25;
    }

    kwScore += kw.internal_link_score * 15;

    const issuesPenalty = Math.min(kw.on_page_issues.length * 2, 10);
    kwScore += 10 - issuesPenalty;

    const gapPenalty = Math.min(kw.missing_topics.length, 10);
    kwScore += 10 - gapPenalty;

    totalScore += kwScore;
  }

  return Math.round(totalScore / keywords.length);
}

function formatTopicLabel(t: MissingTopic): string {
  if (t.kind === "paa") return t.topic;
  if (t.kind === "serp_feature") return t.topic;
  return t.example_heading || t.topic;
}

function summarizeInsight(insight: CompetitorInsight): {
  title: string;
  description: string;
  evidence: string;
} {
  const topEvidence = insight.evidence
    .slice(0, 2)
    .map((e) => `${e.competitor_domain}: ${e.value}`)
    .join(" · ");

  return {
    title: insight.recommendation,
    description: `${insight.observation} You: ${insight.your_value} · Competitors: ${insight.competitor_avg}`,
    evidence: topEvidence,
  };
}

export function computeActionItems(keywords: KeywordData[]): ActionItem[] {
  const items: ActionItem[] = [];

  for (const kw of (keywords ?? [])) {
    // Competitor-grounded insights — now the primary source of "why we're losing"
    for (const insight of kw.competitor_insights) {
      const { title, description, evidence } = summarizeInsight(insight);
      items.push({
        keyword: kw.keyword,
        category: "competitor",
        priority: insight.severity,
        title,
        description,
        evidence,
      });
    }

    // On-page issues
    for (const issue of kw.on_page_issues) {
      const isHighPriority =
        issue.toLowerCase().includes("missing") ||
        issue.toLowerCase().includes("no h1") ||
        issue.toLowerCase().includes("no page exists");
      items.push({
        keyword: kw.keyword,
        category: "on-page",
        priority: isHighPriority ? "high" : "medium",
        title: issue,
        description: `Fix on-page issue for "${kw.keyword}"`,
      });
    }

    // Content gaps — one action per gap, with competitor attribution
    const headingGaps = kw.missing_topics.filter((t) => t.kind === "heading");
    const paaGaps = kw.missing_topics.filter((t) => t.kind === "paa");
    const serpGaps = kw.missing_topics.filter((t) => t.kind === "serp_feature");

    if (headingGaps.length > 0) {
      const topGap = headingGaps[0];
      items.push({
        keyword: kw.keyword,
        category: "content",
        priority: headingGaps.length > 4 ? "high" : "medium",
        title: `Add ${headingGaps.length} missing sections`,
        description: `E.g. "${formatTopicLabel(topGap)}" — covered by ${topGap.frequency} competitors. Full list: ${headingGaps
          .slice(0, 3)
          .map(formatTopicLabel)
          .join(", ")}${headingGaps.length > 3 ? "..." : ""}`,
        evidence: topGap.source_competitors.slice(0, 2).join(" · "),
      });
    }
    if (paaGaps.length > 0) {
      items.push({
        keyword: kw.keyword,
        category: "content",
        priority: "medium",
        title: `Answer ${paaGaps.length} unaddressed PAA questions`,
        description: paaGaps
          .slice(0, 3)
          .map((g) => g.topic)
          .join("; "),
      });
    }
    if (serpGaps.length > 0) {
      items.push({
        keyword: kw.keyword,
        category: "serp",
        priority: "medium",
        title: `${serpGaps.length} SERP-feature opportunities`,
        description: serpGaps.map((g) => g.topic).join("; "),
      });
    }

    // Backlink gaps
    if (kw.backlink_gap.length > 0) {
      const top = kw.backlink_gap.slice(0, 3);
      items.push({
        keyword: kw.keyword,
        category: "backlinks",
        priority: kw.backlink_gap.length > 5 ? "high" : "medium",
        title: `Target ${kw.backlink_gap.length} backlink opportunities`,
        description: `Top targets: ${top
          .map((g) => `${g.source_domain} (OPR ${g.opr_score.toFixed(1)})`)
          .join(", ")}`,
      });
    }

    // Internal link issues
    if (kw.internal_link_score < 0.5) {
      items.push({
        keyword: kw.keyword,
        category: "internal-links",
        priority: kw.internal_link_score < 0.3 ? "high" : "medium",
        title: `Improve internal linking (score: ${(kw.internal_link_score * 100).toFixed(0)}%)`,
        description: kw.internal_link_issues.join("; "),
      });
    }

    // Page speed
    if (kw.page_speed && kw.page_speed.score < 50) {
      items.push({
        keyword: kw.keyword,
        category: "speed",
        priority: "high",
        title: `Fix page speed (score: ${kw.page_speed.score})`,
        description: `LCP: ${kw.page_speed.lcp}s (${kw.page_speed.lcp_rating}), CLS: ${kw.page_speed.cls} (${kw.page_speed.cls_rating})`,
      });
    } else if (kw.page_speed && kw.page_speed.score < 90) {
      items.push({
        keyword: kw.keyword,
        category: "speed",
        priority: "low",
        title: `Optimize page speed (score: ${kw.page_speed.score})`,
        description: `Room for improvement on Core Web Vitals`,
      });
    }

    // Featured snippet opportunity (when already ranking on page 1)
    if (
      kw.serp_features.has_featured_snippet &&
      kw.your_rank !== null &&
      kw.your_rank <= 10
    ) {
      items.push({
        keyword: kw.keyword,
        category: "serp",
        priority: "medium",
        title: "Target featured snippet",
        description: `You're ranking #${kw.your_rank} — add structured content to win the featured snippet`,
      });
    }
  }

  const priorityOrder = { high: 0, medium: 1, low: 2 };
  items.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

  return items;
}

export function aggregateCompetitors(
  keywords: KeywordData[]
): { domain: string; count: number; avgRank: number; keywords: string[] }[] {
  const domainMap = new Map<
    string,
    { ranks: number[]; keywords: string[] }
  >();

  for (const kw of (keywords ?? [])) {
    for (const comp of kw.top_competitors) {
      const existing = domainMap.get(comp.domain) || {
        ranks: [],
        keywords: [],
      };
      existing.ranks.push(comp.rank);
      existing.keywords.push(kw.keyword);
      domainMap.set(comp.domain, existing);
    }
  }

  return Array.from(domainMap.entries())
    .map(([domain, data]) => ({
      domain,
      count: data.ranks.length,
      avgRank: Math.round(
        (data.ranks.reduce((a, b) => a + b, 0) / data.ranks.length) * 10
      ) / 10,
      keywords: data.keywords,
    }))
    .sort((a, b) => b.count - a.count);
}

export function aggregateSerpFeatures(
  keywords: KeywordData[]
): { feature: string; count: number }[] {
  const features = [
    { key: "has_featured_snippet", label: "Featured Snippet" },
    { key: "has_knowledge_panel", label: "Knowledge Panel" },
    { key: "has_video_carousel", label: "Video Carousel" },
    { key: "has_image_pack", label: "Image Pack" },
    { key: "has_local_pack", label: "Local Pack" },
  ] as const;

  return features.map(({ key, label }) => ({
    feature: label,
    count: (keywords ?? []).filter(
      (kw) => kw.serp_features[key as keyof typeof kw.serp_features] === true
    ).length,
  }));
}
