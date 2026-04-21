import type { ReportData } from "./types";

const AGENT_BASE_URL = process.env.AGENT_BASE_URL ?? "http://127.0.0.1:8000";
const AGENT_API_KEY = process.env.AGENT_API_KEY ?? "";
const GRAPH_ID = process.env.AGENT_GRAPH_ID ?? "seo_agent";

const POLL_INTERVAL_MS = 5_000;
const POLL_TIMEOUT_MS = 15 * 60 * 1_000; // 15 min max

function agentHeaders(): HeadersInit {
  const h: HeadersInit = { "Content-Type": "application/json" };
  if (AGENT_API_KEY) h["X-Api-Key"] = AGENT_API_KEY;
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

/** Start a run and return its run_id. Returns 202 immediately. */
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
  const data = (await res.json()) as { run_id?: string };
  if (!data.run_id) {
    throw new Error(
      `POST /runs missing run_id in response. Agent pod may be running old image. Got: ${JSON.stringify(
        data
      )}`
    );
  }
  return data.run_id;
}

/** Poll until status is completed or failed. Returns final output. */
async function pollRun(runId: string): Promise<AgentOutput> {
  const deadline = Date.now() + POLL_TIMEOUT_MS;
  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
    const res = await fetch(`${AGENT_BASE_URL}/runs/${runId}`, {
      headers: agentHeaders(),
    });
    if (!res.ok) throw new Error(`GET /runs/${runId} failed ${res.status}`);
    const data = (await res.json()) as {
      status: string;
      output: AgentOutput | null;
      error: string | null;
    };
    if (data.status === "completed") {
      if (!data.output) throw new Error("Run completed but output is null");
      return data.output;
    }
    if (data.status === "failed") {
      throw new Error(data.error ?? "Agent run failed");
    }
    // status === "running" — keep polling
  }
  throw new Error(
    `Agent run timed out after ${POLL_TIMEOUT_MS / 60_000} minutes`
  );
}

/**
 * Run the agent and return the final state.
 * Starts an async run on the Orkest agent pod, polls until done.
 */
export async function runAgent(
  targetDomain: string,
  keywords: string[]
): Promise<{ threadId: string; output: AgentOutput }> {
  const input = buildAgentInput(targetDomain, keywords);
  const runId = await startRun(input);
  const output = await pollRun(runId);
  return { threadId: runId, output }; // threadId reused for run_id — stored in DB for tracing
}

/** Build the ReportData object the web-app renders from agent output. */
export function toReportData(
  targetDomain: string,
  output: AgentOutput
): ReportData {
  return {
    domain: targetDomain,
    generated_at: new Date().toISOString(),
    keywords: output.results,
  };
}
