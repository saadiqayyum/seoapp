# dg-blog-agent

A LangGraph agent that reviews **stale blogs** and stores structured improvement
suggestions. Built with the same structure as `dg-seo-agent`.

## What it does

```
load_stale_blogs ──(fan-out: one Send per blog)──> analyze_one_blog ──> END
load_stale_blogs ──(no blogs)──────────────────────────────────────> END
```

1. **load_stale_blogs** — pulls the `n` oldest published blogs not updated in the
   last `x` months from MongoDB **A** (`articles`, read-only). `n` (`BLOG_LIMIT`/
   `--limit`) and `x` (`MONTHS_OLD`/`--months`) are graph parameters.
2. **fan-out** — one branch per blog (LangGraph `Send`). With no stale blogs it
   routes straight to `END`.
3. **analyze_one_blog** — reads the blog body from `documents`, asks the LLM what
   to improve, and gets back a full rewritten body (`proposedContent`) plus a
   structured analysis. The result is saved as a **pending suggestion** in
   MongoDB **B** (`blog_suggestions`, read/write). Per-blog failures are recorded
   and never abort the run.

Only the essentials are env vars: the LLM provider/model/key and the two
MongoDB URIs (A read, B write). Everything else (temperature, db/collection
names, site base, default `months`/`limit`) lives in `blog_agent/config.py` and
is passable as graph/CLI params.

## Layout

```
blog_agent/
  config.py                  # env-driven settings (pydantic-settings)
  state.py                   # LangGraph state (TypedDict + concat reducers)
  schema.py                  # BlogAnalysis contract + BlogRef
  llm.py                     # init_chat_model + with_structured_output
  db.py                      # pymongo connections (source A / app B)
  graph.py                   # StateGraph wiring (exports `graph`)
  main.py                    # CLI entry point
  tools/
    fetch_stale_blogs.py     # entry node — query articles
    blog_content.py          # read body + outline from documents
    analyze.py               # LLM call -> BlogAnalysis
    save_suggestion.py       # persist to blog_suggestions (Mongo B)
```

## Setup

```bash
pip install -r requirements.txt        # or: pip install -e .
cp .env.example .env                   # fill in keys + Mongo URIs
```

## Run

```bash
# n=50 blogs not updated in x=6 months
python -m blog_agent.main --months 6 --limit 50

# serve the graph for LangGraph Studio
langgraph dev
```

`langgraph dev` exposes the graph as `blog_agent`; invoke it with state such as
`{ "months_old": 6, "limit": 50 }`.
