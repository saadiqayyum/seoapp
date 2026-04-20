# SEO Dashboard

Next.js dashboard for the LangGraph SEO agent (`../dg-seo-agent`). Users log in, add domains, run keyword audits, and explore the structured results — rankings, competitor-grounded insights, content gaps, page speed, and prioritized action items.

Audits are executed by the agent over HTTP (`@langchain/langgraph-sdk`) and stored in MongoDB so every run is inspectable and, in V2, comparable over time.

---

## Architecture

```
┌──────────────┐     HTTP (LangGraph SDK)      ┌────────────────────┐
│  Next.js app │ ────────────────────────────> │  langgraph dev     │
│ (dashboard,  │                               │  127.0.0.1:2024    │
│  auth, DB)   │ <──── final ReportData ─────  │  (SEO agent graph) │
└──────┬───────┘                               └────────────────────┘
       │
       ▼
┌──────────────┐
│  MongoDB     │  users / domains / audits
│  127.0.0.1   │
└──────────────┘
```

### Audit lifecycle (fire-and-forget + poll)

1. `POST /api/audits` inserts a doc with `status: "pending"` and returns the audit id immediately.
2. A background promise calls `client.runs.wait(threadId, "seo_agent", { input })`. When the agent finishes, the doc is updated to `status: "complete"` with the full `ReportData`.
3. The audit detail page polls `GET /api/audits/:id` every 3s until the status is terminal.
4. Other pages (`/`, `/keywords`, `/competitors`, `/actions`) always render the **latest completed audit** for the current domain.

---

## Tech stack

| Layer | Choice |
|---|---|
| Framework | Next.js 16 (App Router, Turbopack, `src/`) |
| Styling | Tailwind CSS v4 + `@tailwindcss/typography` |
| UI | shadcn/ui + `@base-ui/react` |
| Charts | Recharts |
| Auth | `iron-session` (cookie, stateless) |
| Password | `bcryptjs` |
| Database | MongoDB via the official `mongodb` driver |
| Agent | `@langchain/langgraph-sdk` |
| Package manager | `yarn` |

---

## Getting started

### 1. Install deps

```bash
yarn install
```

### 2. Configure env

Copy `.env.local.example` → `.env.local` and fill in:

```env
MONGO_URI=mongodb://127.0.0.1/muham?retryWrites=true&w=majority&authSource=admin

# LangGraph server (the companion agent repo)
LANGGRAPH_URL=http://127.0.0.1:2024
LANGGRAPH_ASSISTANT_ID=seo_agent

# Session cookie encryption key — generate with:
#   node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
SESSION_PASSWORD=<32+ char random string>

# Admin user — seeded on first request if not present
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=changeme
```

### 3. Start Mongo + the agent + the app

```bash
# Mongo (assumed running on 127.0.0.1:27017)

# Agent (separate shell, from ../dg-seo-agent)
pip install -U "langgraph-cli[inmem]" -e .
langgraph dev --allow-blocking

# Web app
yarn dev
```

Visit `http://localhost:3000` — you'll be redirected to `/login`. Use the admin creds from `.env.local`.

---

## Routes

| Route | Purpose |
|---|---|
| `/login` | Email + password form |
| `/` | Current-domain overview (latest completed audit) |
| `/keywords` | Table of tracked keywords |
| `/keywords/[keyword]` | Keyword deep-dive: competitors, insights, on-page, content gaps, speed |
| `/competitors` | Cross-keyword competitor aggregation |
| `/actions` | Prioritized action items (competitor-grounded + on-page + content + speed) |
| `/report` | Placeholder for the narrative markdown report (disabled in V1) |
| `/domains` | Add / remove / set-current domains |
| `/audits` | Audit history for the current domain |
| `/audits/new` | Run a new audit on the current domain |
| `/audits/[id]` | Single audit view with live polling until complete |

### API

| Route | Method | Purpose |
|---|---|---|
| `/api/auth/login` | POST | Email + password login |
| `/api/auth/logout` | POST | Destroy session |
| `/api/auth/me` | GET | Returns `{ user }` or `{ user: null }` |
| `/api/session` | GET | Returns `{ user, currentDomainId }` |
| `/api/session/current-domain` | POST | Sets current domain in session cookie |
| `/api/domains` | GET/POST | List or create domains |
| `/api/domains/[id]` | DELETE | Remove a domain |
| `/api/audits` | GET/POST | List by `domainId=`, or create |
| `/api/audits/[id]` | GET | Fetch one audit (client polls this) |

All `/api/*` routes except `/api/auth/login` and `/api/auth/me` require auth (enforced by `src/middleware.ts`).

---

## Data model

```ts
users:   { _id, email, passwordHash, createdAt }

domains: { _id, userId, url, label, isActive, createdAt }
         // index: { userId: 1, isActive: 1 }

audits:  {
  _id, userId, domainId,
  keywords: string[],
  status: "pending" | "running" | "complete" | "failed",
  threadId: string | null,
  assistantId: "seo_agent",
  report: ReportData | null,     // the full structured agent output
  error: string | null,
  createdAt, startedAt, completedAt
}
         // indexes: { domainId: 1, createdAt: -1 }, { userId: 1, createdAt: -1 }
```

The `ReportData` shape is defined in `src/lib/types.ts` — it's the same contract the agent returns in its final state.

---

## Project structure

```
src/
├── app/
│   ├── layout.tsx              # ThemeProvider + TooltipProvider + AppShell
│   ├── page.tsx                # Overview (current audit)
│   ├── login/                  # Login page (wrapped in Suspense)
│   ├── domains/                # Manage domains
│   ├── audits/
│   │   ├── page.tsx            # History list
│   │   ├── new/page.tsx        # Keyword input → POST /api/audits
│   │   └── [id]/page.tsx       # Live polling + status view
│   ├── keywords/
│   │   ├── page.tsx
│   │   └── [keyword]/
│   │       ├── page.tsx
│   │       └── keyword-detail-tabs.tsx
│   ├── competitors/, actions/, report/
│   └── api/
│       ├── auth/{login,logout,me}/route.ts
│       ├── session/{route.ts, current-domain/route.ts}
│       ├── domains/{route.ts, [id]/route.ts}
│       └── audits/{route.ts, [id]/route.ts}
│
├── components/
│   ├── layout/
│   │   ├── app-shell.tsx       # Skips sidebar on /login
│   │   ├── app-sidebar.tsx     # Domain switcher + nav + logout
│   │   ├── domain-switcher.tsx # Popover in sidebar header
│   │   ├── empty-state.tsx     # No-domain / no-audit CTAs
│   │   └── header.tsx
│   ├── overview/, keyword-detail/, competitors/, actions/, report/
│   └── ui/                     # shadcn primitives
│
├── lib/
│   ├── db.ts                   # Mongo client + typed collections
│   ├── auth.ts                 # iron-session, admin seeding, credential check
│   ├── domains.ts              # Domain CRUD helpers
│   ├── audits.ts               # Audit lifecycle + background agent run
│   ├── agent-client.ts         # LangGraph SDK wrapper
│   ├── data.ts                 # getSignedInUserState() — the only data entry point
│   ├── computations.ts         # Health score, action items, aggregations
│   ├── constants.ts, types.ts, utils.ts
│
├── hooks/
└── middleware.ts               # Auth guard
```

---

## V1 / V2

### What's in V1

**Auth & multi-tenancy**
- iron-session cookie, bcrypt password hashing
- Hardcoded single admin seeded from `.env.local` on first request
- Middleware redirects unauthenticated users to `/login`, returns 401 on protected API calls

**Domains**
- Per-user domain CRUD with URL normalization (`https://example.com` canonical form)
- Sidebar domain switcher (byword-style) with "Current domain" / "Manage" / "Add"
- Current domain stored in the session cookie; auto-picks the first active domain if none selected

**Audits**
- Fire-and-forget pattern via `src/lib/audits.ts::runAuditInBackground` — POST returns immediately, client polls
- LangGraph SDK integration (`client.runs.wait` on a fresh thread per audit)
- Full lifecycle: `pending → running → complete | failed`, with `startedAt` / `completedAt` timestamps and `error` persisted on failures
- Audit history per domain

**Dashboard**
- All existing pages (`/`, `/keywords`, `/competitors`, `/actions`) now load from the latest completed audit for the current domain
- Empty-state CTAs when the user has no domain or no audit yet
- Competitor-grounded insights card + richer content-gaps card (see companion agent README for the data shape)

**Deferred / placeholders**
- `/report` renders a "Coming soon" card — the markdown synthesiser is intentionally off in V1
- Backlink gap data is not produced by the agent in V1 (no Moz/Ahrefs key wired)

### What's planned for V2

1. **Multi-user** — replace hardcoded admin with real signup + NextAuth (or continue with iron-session and add `/api/auth/signup`). Everything in the data layer is already scoped by `userId`.
2. **Audit comparison / progress tracking** — diff two audits to show improvement after recommendations are implemented. Needs:
   - `/audits/compare?from=...&to=...` route
   - Side-by-side rank / CWV / insight-resolution visualization
   - Highlight which previously-flagged insights are now resolved
3. **Re-enable the markdown report** — add `synthesise_report` as a final node in the agent graph, surface `final_report` on the audit doc, swap `/report` from placeholder to `<MarkdownRenderer content={audit.final_report} />`.
4. **Backlink gap** — once Moz/Ahrefs credentials are available, the agent node exists but is commented out; the UI already renders `backlink_gap` strings.
5. **Streaming progress** — swap `runs.wait` for `runs.stream` and render per-node status on `/audits/[id]`.
6. **Scheduling** — cron-style "audit this domain every Monday" using a job runner.
7. **Export** — CSV/PDF of any completed audit.

### Known limitations of the fire-and-forget pattern

The background agent run lives inside the Next.js process. That's fine for local dev but:

- If you deploy to Vercel, the serverless function will terminate before the agent finishes (audits take minutes).
- If you `yarn dev` restarts mid-run, the audit is orphaned in `pending` / `running` state.

V2 options: externalize the runner to a queue (BullMQ, Inngest, or a small FastAPI sidecar) — or, since the LangGraph platform itself persists runs, use `runs.create` (non-blocking) and have a separate worker poll thread state.
