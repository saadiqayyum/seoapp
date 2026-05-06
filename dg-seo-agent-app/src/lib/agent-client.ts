import type { ReportData } from "./types";

const AGENT_BASE_URL = process.env.AGENT_BASE_URL ?? "http://127.0.0.1:8000";
const AGENT_API_KEY = process.env.AGENT_API_KEY ?? "";
const GRAPH_ID = process.env.AGENT_GRAPH_ID ?? "seo_agent";

const POLL_INTERVAL_MS = 5_000;
const POLL_TIMEOUT_MS = 15 * 60 * 1_000; // 15 min max
// Treat short bursts of gateway errors as transient. Cold-starts and proxy
// hiccups on the deployed LangGraph runtime will routinely produce a 502/503
// for a few seconds. We only abort the audit when the backend stays
// unreachable for a sustained window.
const TRANSIENT_FAILURE_LIMIT = 12; // ~60s of consecutive 502/503/504/network errors
const POLL_REQUEST_TIMEOUT_MS = 30_000;

function agentHeaders(): HeadersInit {
  const h: HeadersInit = { "Content-Type": "application/json" };
  if (AGENT_API_KEY) h["X-API-Key"] = AGENT_API_KEY;
  return h;
}

/** @deprecated kept for audits.ts compatibility */
export function getAssistantId(): string {
  return GRAPH_ID;
}

/** Shape the agent expects as initial state. Matches SEOAgentState in Python. */
interface AgentInput extends Record<string, unknown> {
  target_domain: string;
  keywords: string[];
  results: [];
  final_report: null;
  errors: [];
}

/** Shape returned by the agent when the run completes. */
interface AgentOutput {
  target_domain: string;
  keywords: string[];
  results: ReportData["keywords"];
  final_report: string | null;
  errors: string[];
}

/** Orkest run response shape. */
interface OrkestRunResponse {
  id: string;
  status: string;
  output_data: AgentOutput | null;
  error_message: string | null;
}

export function buildAgentInput(
  targetDomain: string,
  keywords: string[]
): AgentInput {
  return {
    target_domain: targetDomain,
    keywords,
    results: [],
    final_report: null,
    errors: [],
  };
}

/** POST /runs — returns 202 immediately with run id. */
async function startRun(input: AgentInput): Promise<string> {
  const res = await fetch(`${AGENT_BASE_URL}/runs`, {
    method: "POST",
    headers: agentHeaders(),
    body: JSON.stringify({ graph_id: GRAPH_ID, input }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`POST /runs failed ${res.status}: ${text}`);
  }
  const data = (await res.json()) as OrkestRunResponse;
  if (!data.id) {
    throw new Error(`POST /runs missing id in response. Got: ${JSON.stringify(data)}`);
  }
  return data.id;
}

function isTransientStatus(status: number): boolean {
  return status === 502 || status === 503 || status === 504 || status === 408;
}

async function fetchRunStatus(runId: string): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), POLL_REQUEST_TIMEOUT_MS);
  try {
    return await fetch(`${AGENT_BASE_URL}/runs/${runId}`, {
      headers: agentHeaders(),
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}

/** Poll GET /runs/{id} until completed or failed.
 *
 * Tolerates transient gateway/network failures: 502/503/504/408 responses and
 * fetch network errors are retried up to TRANSIENT_FAILURE_LIMIT consecutive
 * polls before the run is declared failed. This survives backend cold-starts
 * and brief proxy outages without aborting long-running audits.
 */
async function pollRun(runId: string): Promise<AgentOutput> {
  const deadline = Date.now() + POLL_TIMEOUT_MS;
  let consecutiveTransient = 0;
  let lastTransientReason: string | null = null;

  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));

    let res: Response;
    try {
      res = await fetchRunStatus(runId);
    } catch (err) {
      // Network failure (DNS, connection reset, abort, etc.) — treat as transient.
      consecutiveTransient++;
      lastTransientReason = err instanceof Error ? err.message : String(err);
      if (consecutiveTransient >= TRANSIENT_FAILURE_LIMIT) {
        throw new Error(
          `Agent unreachable: ${lastTransientReason} (after ${consecutiveTransient} retries)`,
        );
      }
      continue;
    }

    if (isTransientStatus(res.status)) {
      consecutiveTransient++;
      lastTransientReason = `${res.status} ${res.statusText || "gateway error"}`;
      if (consecutiveTransient >= TRANSIENT_FAILURE_LIMIT) {
        throw new Error(
          `Agent unreachable: ${lastTransientReason} (after ${consecutiveTransient} retries). The agent backend appears to be down.`,
        );
      }
      continue;
    }

    if (!res.ok) {
      throw new Error(`GET /runs/${runId} failed ${res.status} ${res.statusText}`);
    }

    consecutiveTransient = 0;
    const data = (await res.json()) as OrkestRunResponse;
    if (data.status === "completed") {
      if (!data.output_data) {
        throw new Error(`Run ${runId} completed but output_data is null`);
      }
      return data.output_data;
    }
    if (data.status === "failed") {
      throw new Error(data.error_message ?? "Agent run failed");
    }
    // status === "running" — keep polling
  }
  throw new Error(`Agent run timed out after ${POLL_TIMEOUT_MS / 60_000} minutes`);
}

/**
 * Run the agent and return the final state.
 * POST /runs returns 202 immediately; polls GET /runs/{id} until done.
 */
export async function runAgent(
  targetDomain: string,
  keywords: string[]
): Promise<{ threadId: string; output: AgentOutput }> {
  const input = buildAgentInput(targetDomain, keywords);
  const runId = await startRun(input);
  const output = await pollRun(runId);
  return { threadId: runId, output };
}

/** Build the ReportData object the web-app renders from agent output. */
export function toReportData(
  targetDomain: string,
  output: AgentOutput
): ReportData {
  return {
    domain: targetDomain,
    generated_at: new Date().toISOString(),
    keywords: output.results ?? [],
  };
}
