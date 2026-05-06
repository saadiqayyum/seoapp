import { audits, AuditDoc, AuditStatus, ObjectId } from "./db";
import { getAssistantId, runAgent, toReportData } from "./agent-client";
import { getDomain } from "./domains";
import type { KeywordData, ReportData } from "./types";

export interface AuditSummary {
  id: string;
  domainId: string;
  keywords: string[];
  status: AuditStatus;
  createdAt: string;
  completedAt: string | null;
  error: string | null;
  hasReport: boolean;
}

export interface AuditDetail extends AuditSummary {
  report: ReportData | null;
}

function summarize(doc: AuditDoc): AuditSummary {
  return {
    id: doc._id.toString(),
    domainId: doc.domainId.toString(),
    keywords: doc.keywords,
    status: doc.status,
    createdAt: doc.createdAt.toISOString(),
    completedAt: doc.completedAt?.toISOString() ?? null,
    error: doc.error,
    hasReport: doc.report !== null,
  };
}

export async function listAudits(
  userId: string,
  domainId: string,
): Promise<AuditSummary[]> {
  const col = await audits();
  const docs = await col
    .find({
      userId: new ObjectId(userId),
      domainId: new ObjectId(domainId),
    })
    .sort({ createdAt: -1 })
    .toArray();
  return docs.map(summarize);
}

export async function getAuditDetail(
  userId: string,
  auditId: string,
): Promise<AuditDetail | null> {
  if (!ObjectId.isValid(auditId)) return null;
  const col = await audits();
  const doc = await col.findOne({
    _id: new ObjectId(auditId),
    userId: new ObjectId(userId),
  });
  if (!doc) return null;
  return { ...summarize(doc), report: doc.report };
}

export interface DomainOverview {
  keywords: KeywordData[];          // deduped, newest entry per keyword
  totalAudits: number;              // count of completed audits for this domain
  lastCompletedAt: string | null;   // ISO date of the most recent completed audit
}

/**
 * Single fetcher for the overview dashboard. Combines aggregated keyword data
 * with audit-level metadata so the dashboard header can show the user exactly
 * what scope the page is summarizing (e.g. "Across 12 keywords from 4 audits").
 */
export async function getDomainOverview(
  userId: string,
  domainId: string,
): Promise<DomainOverview> {
  const col = await audits();
  const docs = await col
    .find({
      userId: new ObjectId(userId),
      domainId: new ObjectId(domainId),
      status: "complete",
    })
    .sort({ completedAt: -1 })
    .toArray();

  const seen = new Map<string, KeywordData>();
  for (const doc of docs) {
    if (!doc.report) continue;
    for (const kw of doc.report.keywords) {
      if (!seen.has(kw.keyword)) seen.set(kw.keyword, kw);
    }
  }

  return {
    keywords: Array.from(seen.values()),
    totalAudits: docs.length,
    lastCompletedAt: docs[0]?.completedAt?.toISOString() ?? null,
  };
}

/**
 * Aggregate keyword data across every completed audit for a domain.
 *
 * Each audit doc is one run with its own keyword set. The /keywords page
 * needs the union of keywords ever audited for a domain — deduped, with the
 * newest entry per keyword winning so the displayed metrics reflect the most
 * recent run that touched that keyword.
 */
export async function getAggregatedKeywordsForDomain(
  userId: string,
  domainId: string,
): Promise<KeywordData[]> {
  const col = await audits();
  const docs = await col
    .find({
      userId: new ObjectId(userId),
      domainId: new ObjectId(domainId),
      status: "complete",
    })
    .sort({ completedAt: -1 })
    .toArray();

  const seen = new Map<string, KeywordData>();
  for (const doc of docs) {
    if (!doc.report) continue;
    for (const kw of doc.report.keywords) {
      if (!seen.has(kw.keyword)) seen.set(kw.keyword, kw);
    }
  }
  return Array.from(seen.values());
}

export async function getLatestCompleteAudit(
  userId: string,
  domainId: string,
): Promise<AuditDetail | null> {
  const col = await audits();
  const doc = await col.findOne(
    {
      userId: new ObjectId(userId),
      domainId: new ObjectId(domainId),
      status: "complete",
    },
    { sort: { completedAt: -1 } },
  );
  if (!doc) return null;
  return { ...summarize(doc), report: doc.report };
}

export async function createAudit(
  userId: string,
  domainId: string,
  keywords: string[],
): Promise<AuditSummary> {
  const domain = await getDomain(userId, domainId);
  if (!domain) throw new Error("Domain not found");
  if (keywords.length === 0) throw new Error("At least one keyword is required");

  const col = await audits();
  const doc: AuditDoc = {
    _id: new ObjectId(),
    userId: new ObjectId(userId),
    domainId: new ObjectId(domainId),
    keywords,
    status: "pending",
    threadId: null,
    assistantId: getAssistantId(),
    report: null,
    error: null,
    createdAt: new Date(),
    startedAt: null,
    completedAt: null,
  };
  await col.insertOne(doc);

  // Fire-and-forget: kick off the agent run asynchronously.
  // The route returns immediately; the client polls GET /api/audits/:id.
  void runAuditInBackground(doc._id.toString(), domain.url, keywords);

  return summarize(doc);
}

async function runAuditInBackground(
  auditId: string,
  targetDomain: string,
  keywords: string[],
): Promise<void> {
  const col = await audits();
  const objectId = new ObjectId(auditId);

  try {
    await col.updateOne(
      { _id: objectId },
      { $set: { status: "running", startedAt: new Date() } },
    );

    const { threadId, output } = await runAgent(targetDomain, keywords);
    const report = toReportData(targetDomain, output);

    await col.updateOne(
      { _id: objectId },
      {
        $set: {
          status: "complete",
          threadId,
          report,
          completedAt: new Date(),
        },
      },
    );
  } catch (e) {
    const message = e instanceof Error ? e.message : "Agent run failed";
    console.error(`[audit ${auditId}] ${message}`, e);
    await col
      .updateOne(
        { _id: objectId },
        {
          $set: {
            status: "failed",
            error: message,
            completedAt: new Date(),
          },
        },
      )
      .catch((err) => console.error("Failed to persist audit failure:", err));
  }
}
