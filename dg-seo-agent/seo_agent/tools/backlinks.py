"""URL-level backlink gap analysis — free, no paid backlink API.

For each keyword, find external pages that mention/link to the competitor URLs
ranking on top, but not to the user's ranking URL. Source domains are scored
by OpenPageRank so the gap can be sorted by authority.

Two free APIs:
- SerpAPI (already in stack): query Google for `"<exact-url>" -site:<domain>` to
  surface external pages referencing that specific URL.
- OpenPageRank: free 1000 req/day, returns a 0-10 PageRank-style score per domain.

This is NOT an exhaustive backlink index. It surfaces the most visible linking
pages Google indexes for that URL string. The report makes that tradeoff explicit.
"""

import logging
from collections import defaultdict
from urllib.parse import urlparse

import requests

from seo_agent.cache.manager import cached_call
from seo_agent.config import settings
from seo_agent.state import BacklinkGap

logger = logging.getLogger(__name__)

SERPAPI_BASE = "https://serpapi.com/search"
OPR_API_BASE = "https://openpagerank.com/api/v1.0/getPageRank"
MAX_LINKERS_PER_URL = 30      # SerpAPI results scanned per ranking URL
OPR_BATCH_SIZE = 100          # OPR endpoint accepts 100 domains per call
MAX_GAPS_PER_KEYWORD = 20     # cap on returned BacklinkGap entries
OPR_CACHE_TTL_HOURS = 24 * 7  # OpenPageRank scores are stable, cache 7d


def _domain_of(url: str) -> str:
    """Extract the bare domain from a URL (drops scheme, www, path, query)."""
    if not url:
        return ""
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:
        return ""


def _fetch_url_linkers(target_url: str, api_key: str) -> list[str]:
    """SerpAPI: find pages indexed by Google that reference target_url.

    Returns the list of source URLs (one per organic result).
    Excludes self-references via `-site:<target_domain>`.
    """
    target_domain = _domain_of(target_url)
    if not target_domain:
        return []

    query = f'"{target_url}" -site:{target_domain}'
    params = {
        "q": query,
        "num": MAX_LINKERS_PER_URL,
        "api_key": api_key,
        "engine": "google",
    }
    response = requests.get(SERPAPI_BASE, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    return [r.get("link", "") for r in data.get("organic_results", []) if r.get("link")]


def _fetch_opr_batch(domains: tuple[str, ...], api_key: str) -> dict[str, float]:
    """OpenPageRank: batch-fetch scores for up to 100 domains.

    Tuple input (not list) so the cache key is hashable and deterministic.
    """
    if not domains:
        return {}

    params = [("domains[]", d) for d in domains]
    response = requests.get(
        OPR_API_BASE,
        params=params,
        headers={"API-OPR": api_key},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    scores: dict[str, float] = {}
    for entry in data.get("response", []):
        d = entry.get("domain", "").lower()
        pr = entry.get("page_rank_decimal")
        if not d or pr is None:
            continue
        try:
            scores[d] = float(pr)
        except (TypeError, ValueError):
            scores[d] = 0.0
    return scores


def _opr_scores(domains: list[str]) -> dict[str, float]:
    """Score every domain via OpenPageRank, batching + caching transparently.

    Returns {domain: score 0.0-10.0}. Missing scores default to 0.0 at read time.
    """
    api_key = settings.openpagerank_api_key
    unique = sorted({d for d in domains if d})
    if not unique:
        return {}
    if not api_key:
        logger.warning("OPENPAGERANK_API_KEY not set — backlink gaps will be unscored")
        return {}

    scores: dict[str, float] = {}
    for i in range(0, len(unique), OPR_BATCH_SIZE):
        chunk = tuple(unique[i:i + OPR_BATCH_SIZE])
        try:
            chunk_scores = cached_call(
                _fetch_opr_batch,
                chunk,
                api_key,
                ttl_hours=OPR_CACHE_TTL_HOURS,
            )
            scores.update(chunk_scores)
        except Exception as e:
            logger.warning("OpenPageRank batch failed (%d domains): %s", len(chunk), e)

    return scores


def _linker_domains(target_url: str) -> set[str]:
    """Source domains that Google indexes as referencing target_url.

    Wraps SerpAPI call in cached_call. Excludes the target's own domain.
    Returns empty set on failure (per-URL errors are logged but not raised).
    """
    if not target_url or not settings.serpapi_key:
        return set()

    target_domain = _domain_of(target_url)
    try:
        sources = cached_call(_fetch_url_linkers, target_url, settings.serpapi_key)
    except Exception as e:
        logger.warning("SerpAPI linker lookup failed for %s: %s", target_url, e)
        return set()

    return {
        d for s in sources
        if (d := _domain_of(s)) and d != target_domain
    }


def find_backlink_gaps_for_keyword(
    your_url: str | None,
    competitor_urls: list[str],
) -> list[BacklinkGap]:
    """Per-keyword URL-level backlink gap.

    Args:
        your_url: The user's ranking URL for this keyword (None if not ranking).
        competitor_urls: Specific competitor URLs ranking on top for this keyword.

    Returns:
        BacklinkGap entries sorted by (links_to_competitors_count desc, opr_score desc).
        Empty list if no competitors or SerpAPI unavailable.
    """
    if not competitor_urls:
        return []
    if not settings.serpapi_key:
        logger.warning("SERPAPI_KEY not set — cannot compute backlink gaps")
        return []

    competitor_linkers: dict[str, set[str]] = {
        url: _linker_domains(url) for url in competitor_urls
    }
    your_linkers: set[str] = _linker_domains(your_url) if your_url else set()

    domain_to_competitors: dict[str, list[str]] = defaultdict(list)
    for comp_url, linkers in competitor_linkers.items():
        for source_domain in linkers:
            if source_domain in your_linkers:
                continue
            domain_to_competitors[source_domain].append(comp_url)

    if not domain_to_competitors:
        return []

    opr = _opr_scores(list(domain_to_competitors.keys()))

    gaps: list[BacklinkGap] = [
        {
            "source_domain": domain,
            "opr_score": opr.get(domain, 0.0),
            "links_to_competitors": comp_urls,
            "links_to_you": False,
        }
        for domain, comp_urls in domain_to_competitors.items()
    ]
    gaps.sort(
        key=lambda g: (len(g["links_to_competitors"]), g["opr_score"]),
        reverse=True,
    )
    return gaps[:MAX_GAPS_PER_KEYWORD]


def find_backlink_gaps_node(state: dict) -> dict:
    """LangGraph node: per-keyword URL-level backlink gap analysis."""
    results = state.get("results", [])
    errors = state.get("errors", [])

    if not settings.serpapi_key:
        logger.warning("SERPAPI_KEY not set — skipping backlink analysis")
        for kw in results:
            kw["backlink_gap"] = []
        return {**state, "results": results, "errors": errors}

    for kw in results:
        keyword = kw["keyword"]
        your_url = kw.get("your_url")
        comp_urls = [c["url"] for c in kw.get("top_competitors", []) if c.get("url")]

        if not comp_urls:
            kw["backlink_gap"] = []
            continue

        try:
            gaps = find_backlink_gaps_for_keyword(your_url, comp_urls)
            kw["backlink_gap"] = gaps
            logger.info(
                "Backlink gap for '%s': %d source domains found across %d competitor URLs",
                keyword, len(gaps), len(comp_urls),
            )
        except Exception as e:
            error_msg = f"[find_backlink_gaps] keyword='{keyword}' error: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            kw["backlink_gap"] = []

    return {**state, "results": results, "errors": errors}
