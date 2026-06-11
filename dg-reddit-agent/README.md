# dg-reddit-agent

A LangGraph agent that discovers relevant Reddit threads for a set of keywords by
**searching Google first** (via SerpAPI, `site:reddit.com <keyword>`), fetching the
threads Google surfaces, and producing a report with a per-thread summary, relevance,
and a copy-pastable suggested reply.

Architecturally it mirrors [`dg-seo-agent`](../dg-seo-agent): a linear LangGraph pipeline
of sync nodes, served via the LangGraph server, using the same SerpAPI + Gemini stack.

## Pipeline

```
discover_threads  ->  fetch_threads  ->  analyze_threads  ->  synthesise_report
(SerpAPI Google)      (reddit *.json)    (Gemini)             (markdown report)
```

## Setup

```bash
cd dg-reddit-agent
python -m venv .venv && .venv\Scripts\activate    # Windows
pip install -r requirements.txt
copy .env.example .env                            # then fill in keys
```

Required env: `SERPAPI_KEY`, `GOOGLE_API_KEY`. Optional: `REDDIT_BEARER_TOKEN` (set it if
anonymous reddit `*.json` reads return 403 in your environment).

## Run (CLI)

```bash
python -m reddit_agent.main --keywords "system design interview" "grokking the coding interview"
```

Outputs `output/reddit_report.md` and `output/report_data.json`.

## Run (server)

```bash
langgraph dev --allow-blocking --port 2025
```

Then start a run and poll:

```
POST /runs   { "graph_id": "reddit_agent", "input": { "keywords": ["..."], "max_threads_per_keyword": 10, "results": [], "final_report": null, "errors": [] } }
GET  /runs/{id}   ->   output_data.final_report  +  output_data.results
```

The port is deliberately different from `dg-seo-agent` (2024) so both can run together.
