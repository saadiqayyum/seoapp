export type WebVitalRating = "FAST" | "AVERAGE" | "SLOW";

export interface SerpFeatures {
  has_featured_snippet: boolean;
  has_knowledge_panel: boolean;
  has_video_carousel: boolean;
  has_image_pack: boolean;
  has_local_pack: boolean;
  people_also_ask: string[];
}

export interface Competitor {
  rank: number;
  url: string;
  title: string;
  domain: string;
}

export interface PageSpeed {
  score: number;
  lcp: number;
  lcp_rating: WebVitalRating;
  fcp: number;
  fcp_rating: WebVitalRating;
  cls: number;
  cls_rating: WebVitalRating;
  inp: number;
  inp_rating: WebVitalRating;
  ttfb: number;
  ttfb_rating: WebVitalRating;
}

export interface RawCompetitorData {
  url: string;
  title: string;
  meta_description: string;
  h1: string[];
  h2: string[];
  h3: string[];
  word_count: number;
  has_schema: boolean;
  internal_links: number;
  external_links: number;
}

export type YourPageData = RawCompetitorData;

export type MissingTopicKind = "heading" | "paa" | "serp_feature";

export interface MissingTopic {
  topic: string;
  example_heading: string;
  level: "H2" | "H3";
  frequency: number;
  source_competitors: string[];
  kind: MissingTopicKind;
}

export interface InsightEvidence {
  competitor_url: string;
  competitor_domain: string;
  value: string;
}

export type InsightCategory =
  | "word_count"
  | "schema"
  | "headings"
  | "meta"
  | "internal_links"
  | "external_links"
  | "title";

export type InsightSeverity = "high" | "medium" | "low";

export interface CompetitorInsight {
  category: InsightCategory;
  observation: string;
  severity: InsightSeverity;
  recommendation: string;
  your_value: string;
  competitor_avg: string;
  evidence: InsightEvidence[];
}

export interface BacklinkGap {
  source_domain: string;
  opr_score: number;
  links_to_competitors: string[];
  links_to_you: boolean;
}

export interface KeywordData {
  keyword: string;
  your_rank: number | null;
  your_url: string | null;
  your_page: number | null;
  serp_features: SerpFeatures;
  top_competitors: Competitor[];
  on_page_issues: string[];
  missing_topics: MissingTopic[];
  backlink_gap: BacklinkGap[];
  internal_link_score: number;
  internal_link_issues: string[];
  page_speed: PageSpeed | null;
  your_page_data: YourPageData | null;
  raw_competitor_data: RawCompetitorData[];
  competitor_insights: CompetitorInsight[];
}

export interface ReportData {
  domain: string;
  generated_at: string;
  keywords: KeywordData[];
}

export interface ActionItem {
  keyword: string;
  category:
    | "on-page"
    | "content"
    | "backlinks"
    | "internal-links"
    | "speed"
    | "serp"
    | "competitor";
  priority: "high" | "medium" | "low";
  title: string;
  description: string;
  evidence?: string;
}
