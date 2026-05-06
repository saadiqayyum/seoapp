import { notFound, redirect } from "next/navigation";
import { Header } from "@/components/layout/header";
import { getSignedInUserState } from "@/lib/data";
import { getAggregatedKeywordsForDomain } from "@/lib/audits";
import { RankPositionBadge } from "@/components/keyword-detail/rank-position-badge";
import { SerpFeaturesIcons } from "@/components/keyword-detail/serp-features-icons";
import { KeywordDetailTabs } from "./keyword-detail-tabs";
import { Separator } from "@/components/ui/separator";

export default async function KeywordDetailPage({
  params,
}: {
  params: Promise<{ keyword: string }>;
}) {
  const { keyword: encodedKeyword } = await params;
  const keyword = decodeURIComponent(encodedKeyword);

  const state = await getSignedInUserState();
  if (state.state === "unauthenticated") redirect("/login");
  if (state.state === "no-domain" || state.state === "no-audit") redirect("/");

  const { domain, user } = state.ctx;
  const keywords = await getAggregatedKeywordsForDomain(user.userId, domain.id);
  const kw = keywords.find((k) => k.keyword === keyword);
  if (!kw) return notFound();

  return (
    <>
      <Header
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "Keywords", href: "/keywords" },
          { label: kw.keyword },
        ]}
      />
      <div className="flex-1 space-y-6 p-4 md:p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div className="space-y-2">
            <h2 className="text-2xl font-bold tracking-tight">
              {kw.keyword}
            </h2>
            {kw.your_url ? (
              <p className="text-sm text-muted-foreground break-all">
                {kw.your_url}
              </p>
            ) : (
              <p className="text-sm text-amber-600 dark:text-amber-400">
                No ranking page found for this keyword
              </p>
            )}
          </div>
          <RankPositionBadge rank={kw.your_rank} page={kw.your_page} />
        </div>

        <SerpFeaturesIcons features={kw.serp_features} />
        <Separator />

        <KeywordDetailTabs keyword={kw} />
      </div>
    </>
  );
}
