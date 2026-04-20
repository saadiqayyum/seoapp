import { Client } from "@langchain/langgraph-sdk";
import type { ReportData } from "./types";

const url = process.env.LANGGRAPH_URL ?? "http://127.0.0.1:2024";
const assistantId = process.env.LANGGRAPH_ASSISTANT_ID ?? "seo_agent";

export function getAgentClient(): Client {
  return new Client({ apiUrl: url });
}

export function getAssistantId(): string {
  return assistantId;
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
  keywords: string[],
): AgentInput {
  return {
    target_domain: targetDomain,
    keywords,
    results: [],
    final_report: null,
    errors: [],
  };
}

/**
 * Run the agent end-to-end and return the final state.
 *
 * Uses `runs.wait` which blocks until the graph terminates and returns the
 * final state values. Thread is created fresh per run.
 */
export async function runAgent(
  targetDomain: string,
  keywords: string[],
): Promise<{ threadId: string; output: AgentOutput }> {
  const client = getAgentClient();

  const thread = await client.threads.create();
  const threadId = thread.thread_id;

  const result = (await client.runs.wait(threadId, assistantId, {
    input: buildAgentInput(targetDomain, keywords),
  })) as unknown as AgentOutput;

  return { threadId, output: result };
}

/** Build the ReportData object the web-app renders from agent output. */
export function toReportData(
  targetDomain: string,
  output: AgentOutput,
): ReportData {
  return {
    domain: targetDomain,
    generated_at: new Date().toISOString(),
    keywords: output.results,
  };
}
