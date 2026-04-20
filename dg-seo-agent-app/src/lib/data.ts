import { getCurrentDomainId, getSession } from "./auth";
import { getLatestCompleteAudit } from "./audits";
import { getDomain, type DomainSummary } from "./domains";
import type { ReportData } from "./types";

export interface CurrentAuditContext {
  user: { userId: string; email: string };
  domain: DomainSummary;
  auditId: string;
  report: ReportData;
}

/**
 * Load the current-domain's most recent completed audit for the signed-in
 * user. Returns null when any prerequisite (auth, current domain, completed
 * audit) is missing — pages render empty states in that case.
 */
export async function getCurrentAudit(): Promise<CurrentAuditContext | null> {
  const session = await getSession();
  if (!session.userId) return null;

  const domainId = await getCurrentDomainId(session);
  if (!domainId) return null;

  const [domain, audit] = await Promise.all([
    getDomain(session.userId, domainId),
    getLatestCompleteAudit(session.userId, domainId),
  ]);
  if (!domain || !audit || !audit.report) return null;

  return {
    user: { userId: session.userId, email: session.email! },
    domain,
    auditId: audit.id,
    report: audit.report,
  };
}

/** True when the user is signed in but has no domain yet. */
export async function getSignedInUserState(): Promise<
  | { state: "unauthenticated" }
  | { state: "no-domain" }
  | { state: "no-audit"; domain: DomainSummary }
  | { state: "ready"; ctx: CurrentAuditContext }
> {
  const session = await getSession();
  if (!session.userId) return { state: "unauthenticated" };

  const domainId = await getCurrentDomainId(session);
  if (!domainId) return { state: "no-domain" };

  const domain = await getDomain(session.userId, domainId);
  if (!domain) return { state: "no-domain" };

  const audit = await getLatestCompleteAudit(session.userId, domainId);
  if (!audit || !audit.report) return { state: "no-audit", domain };

  return {
    state: "ready",
    ctx: {
      user: { userId: session.userId, email: session.email! },
      domain,
      auditId: audit.id,
      report: audit.report,
    },
  };
}
