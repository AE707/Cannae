# Cannae — AI Business Operating System
## Context for Claude Code

---

## What Is Cannae

Cannae is an AI-powered business operating system named after Hannibal's Battle of Cannae (216 BC).
The brand philosophy: outthink larger forces through superior preparation and memory.

The product has two pillars:
- **AI Command Center** (MVP — build this first): A council of specialized AI agents (CEO, Coach, SEO, CFO)
  with persistent graph memory that connects decisions across time.
- **Knowledge Marketplace** (v2 — defer until ~100 paying users validate memory layer): Human coaches
  sell content; AI agents study it and apply it to the user's own decision history.

Core product thesis: no existing tool combines multi-agent personas + relational graph memory +
a full workspace suite simultaneously. The memory layer IS the differentiator.

---

## MVP Scope (AI Command Center only)

### Phase 1 — Build now
- CEO agent + Coach agent only
- Hybrid memory layer (ChromaDB vector + Mem0 graph)
- LangGraph orchestration with agent handoff
- `/council` UI route: agent selector, chat, memory sidebar, handoff indicator

### Defer to Phase 2
- SEO and CFO agents
- Knowledge Marketplace
- Supabase migration (use SQLite locally until Phase 1 is validated)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11+) |
| Orchestration | LangGraph |
| Vector memory | ChromaDB (embedded) |
| Graph memory | Mem0 + FalkorDB |
| LLM | Anthropic Claude API — `claude-sonnet-4-20250514` |
| Frontend | Plain HTML/CSS/JS (static/) — no framework in Phase 1 |
| Database | SQLite via SQLAlchemy (local) → Supabase + pgvector (Phase 2) |
| Auth | Simple JWT (Phase 1); full RBAC in Phase 2 |

---

## Project Architecture

```
cannaec/
├── CLAUDE.md                  ← you are here; read this every session
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── app.py                     ← FastAPI entry point; registers all routers
│
├── core/
│   ├── config.py              ← Pydantic Settings; reads .env
│   ├── database.py            ← SQLAlchemy engine + session factory
│   ├── auth.py                ← JWT helpers, dependency injection
│   └── constants.py           ← Shared enums, literals, model names
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          ← BaseAgent class: invoke(), stream(), memory hooks
│   ├── ceo_agent.py           ← CEO persona, system prompt, tool list
│   ├── coach_agent.py         ← Coach persona, system prompt, tool list
│   └── council.py             ← LangGraph StateGraph: orchestration + handoff logic
│
├── memory/
│   ├── __init__.py
│   ├── vector_store.py        ← ChromaDB wrapper: add(), query()
│   ├── graph_memory.py        ← Mem0 wrapper: add_decision(), get_context()
│   └── memory_layer.py        ← Unified interface: write to both, merge reads
│
├── routes/
│   ├── __init__.py
│   ├── council.py             ← POST /council/chat, GET /council/memory
│   ├── chat.py                ← General chat endpoints (non-council)
│   └── memory.py              ← Memory CRUD endpoints
│
├── services/
│   ├── llm.py                 ← Anthropic client singleton + streaming helper
│   └── search.py              ← Web search (SearXNG or Tavily)
│
├── static/
│   ├── index.html             ← App shell; loads council.js for /council route
│   ├── style.css
│   └── js/
│       ├── council.js         ← Council UI: agent selector, chat, memory sidebar
│       └── app.js             ← Shared utilities
│
├── docs/
│   └── architecture.md        ← Running notes on decisions made
│
└── data/                      ← gitignored; local runtime data
    └── .gitkeep
```

---

## Key Conventions

### Python
- Python 3.11+
- Type hints everywhere — no untyped functions
- Pydantic models for all request/response schemas
- Async throughout — use `async def` for all route handlers and agent calls
- Config via `core/config.py` (Pydantic BaseSettings) — never read `os.environ` directly
- Never hardcode the model name — use `constants.CLAUDE_MODEL`

### API
- All routes prefixed: `/api/v1/`
- Consistent response envelope: `{ "data": ..., "error": null }`
- Agent streaming via Server-Sent Events (SSE) — not WebSockets

### Memory
- Every agent turn: write to BOTH vector_store and graph_memory before returning response
- Memory keys: `user_id:agent_id:timestamp` — never collide across users
- Graph memory stores: decisions, entities, relationships — NOT raw chat history (that's vector)

### LangGraph
- One `CouncilState` TypedDict shared across all nodes
- Nodes: `retrieve_memory` → `route_to_agent` → `ceo_node | coach_node` → `handoff_check` → `write_memory`
- Handoff: CEO sets `state["handoff_to"] = "coach"` to trigger Coach continuation

### Frontend
- No npm, no bundler — vanilla JS modules in static/js/
- Council UI re-uses fetch + SSE for streaming — same pattern as chat.js
- Dark/light theme via CSS variables on :root

---

## Agent Personas (reference)

### CEO Agent
- Role: strategy, prioritization, resource allocation, major decisions
- Tone: direct, confident, data-informed — thinks in systems and leverage
- Memory focus: past strategic decisions, pivots, resource commitments
- Signature: always ends with a "Next highest-leverage action"

### Coach Agent  
- Role: accountability, goal tracking, behavioral loops, habit systems
- Tone: warm but challenging — asks the hard question back
- Memory focus: commitments made, patterns of follow-through/avoidance
- Signature: always surfaces one past commitment before responding to a new one

---

## Environment Variables

See `.env.example`. Critical ones:
```
ANTHROPIC_API_KEY=sk-ant-...
CHROMADB_PATH=./data/chroma
MEM0_API_KEY=...              # or self-host FalkorDB
DATABASE_URL=sqlite:///./data/cannae.db
JWT_SECRET=...
```

---

## Current Build Status

- [ ] Project scaffold (folders, requirements.txt, app.py shell)
- [ ] core/config.py + core/constants.py
- [ ] memory/vector_store.py (ChromaDB)
- [ ] memory/graph_memory.py (Mem0)
- [ ] memory/memory_layer.py (unified)
- [ ] agents/base_agent.py
- [ ] agents/ceo_agent.py (system prompt + invoke)
- [ ] agents/coach_agent.py
- [ ] agents/council.py (LangGraph graph)
- [ ] routes/council.py
- [ ] app.py (full, with all routers)
- [ ] static/index.html + council.js
- [ ] .env.example + requirements.txt

---

## Architecture Reference (Odysseus-inspired)

Cannae's layout is inspired by Odysseus (a self-hosted AI workspace):
- Same FastAPI pattern: `app.py` → `routes/` → `services/`
- Same ChromaDB embedded setup
- Same static/ frontend approach (no build step)
- Key additions: `agents/` layer, `memory/` layer, LangGraph orchestration

Do not import or depend on Odysseus. Use it only as a structural reference.

---

## Critical Rules for Claude Code

1. Always check `CLAUDE.md` at the start of each session — state the current build status
2. Never install a dependency without adding it to `requirements.txt`
3. Never read `os.environ` directly — always use `core/config.py` Settings
4. Never hardcode `ANTHROPIC_API_KEY` or any secret
5. After each file is created, update the build status checklist above
6. When in doubt about memory architecture, favor the unified `memory_layer.py` interface — don't bypass it
7. MVP scope is firm: CEO + Coach only. Do not add SEO/CFO agents until told to.
