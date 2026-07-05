# Cannae — AI Business Operating System

> *Outthink larger forces through superior preparation and memory.*

An AI‑powered business operating system that gives you a **council of specialized AI agents** (CEO, Coach, SEO, CFO) backed by a **persistent graph memory** that connects every decision across time.  
The memory layer is the core differentiator—combining vector search (ChromaDB) with a relational graph (Mem0 + FalkorDB) so agents can recall past commitments, strategies, and outcomes.

---

## 📖 What Is Cannae?

Cannae is named after Hannibal’s Battle of Cannae (216 BC), where a smaller force triumphed through superior preparation and memory.  
The product has two pillars:

| Pillar | Description |
|--------|-------------|
| **AI Command Center (MVP)** | A council of AI agents (CEO, Coach, SEO, CFO) that share a hybrid memory layer. This is the focus of Phase 1. |
| **Knowledge Marketplace (v2)** | Human coaches sell content; AI agents study it and apply it to the user’s own decision history. Deferred until the memory layer is validated with ~100 paying users. |

**Core thesis:** No existing tool combines multi‑agent personas + relational graph memory + a full workspace suite simultaneously. The memory layer **is** the differentiator.

---

## ✨ Key Features

- **Multi‑Agent Council** – CEO (strategy), Coach (accountability), plus planned SEO and CFO agents.
- **Hybrid Memory** – Vector store (ChromaDB) for semantic search + graph store (Mem0 + FalkorDB) for decisions, entities, and relationships.
- **LangGraph Orchestration** – StateGraph with nodes for memory retrieval, agent routing, handoff checks, and memory writes.
- **Streaming API** – Agent responses streamed via Server‑Sent Events (SSE).
- **Zero‑Build Frontend** – Plain HTML/CSS/JS (static/), no npm or bundler.
- **Secure defaults** – JWT auth (Phase 1), RBAC planned for Phase 2.
- **Local‑first dev** – SQLite via SQLAlchemy; migrate to Supabase + pgvector in Phase 2.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (Python 3.11+) |
| **Orchestration** | LangGraph |
| **Vector Memory** | ChromaDB (embedded) |
| **Graph Memory** | Mem0 + FalkorDB |
| **LLM** | Anthropic Claude API – `claude-sonnet-4-20250514` |
| **Frontend** | Plain HTML/CSS/JS (static/) |
| **Database** | SQLite via SQLAlchemy (local) → Supabase + pgvector (Phase 2) |
| **Auth** | Simple JWT (Phase 1); full RBAC (Phase 2) |
| **Other** | Pydantic settings, python‑jose, passlib, httpx, langchain‑anthropic |

---

## 🗂️ Project Architecture

```
cannaec/
├── CLAUDE.md                  # project instructions & build status
├── README.md                  # this file
├── .env.example
├── .gitignore
├── requirements.txt
├── app.py                     # FastAPI entry point; registers all routers
│
├── core/
│   ├── config.py              # Pydantic Settings; reads .env
│   ├── database.py            # SQLAlchemy engine + session factory
│   ├── auth.py                # JWT helpers, dependency injection
│   └── constants.py           # Shared enums, literals, model names
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # BaseAgent: invoke(), stream(), memory hooks
│   ├── ceo_agent.py           # CEO persona, system prompt, tool list
│   ├── coach_agent.py         # Coach persona, system prompt, tool list
│   tool list
│   └── council.py             # LangGraph StateGraph: orchestration + handoff logic
│
├── memory/
│   ├── __init__.py
│   ├── vector_store.py        # ChromaDB wrapper: add(), query()
│   ├── graph_memory.py        # Mem0 wrapper: add_decision(), get_context()
│   └── memory_layer.py        # Unified interface: write to both, merge reads
│
├── routes/
│   ├── __init__.py
│   ├── council.py             # POST /council/chat, GET /council/memory
│   ├── chat.py                # General chat endpoints (non‑council)
│   └── memory.py              # Memory CRUD endpoints
│
├── services/
│   ├── llm.py                 # Anthropic client singleton + streaming helper
│   └── search.py              # Web search (SearXNG or Tavily)
│
├── static/
│   ├── index.html             # App shell; loads council.js for /council route
│   ├── style.css
│   └── js/
│       ├── council.js         # Council UI: agent selector, chat, memory sidebar
│       └── app.js             # Shared utilities
│
├── docs/
│   └── architecture.md        # Running notes on decisions made
│
└── data/                      # gitignored; local runtime data
    └── .gitkeep
```

### Conventions

- **Python 3.11+**, type hints everywhere, Pydantic models for all schemas.
- **Async throughout** – `async def` for route handlers and agent calls.
- **Config via `core/config.py`** – never read `os.environ` directly.
- **API prefix** – `/api/v1/` with envelope `{ "data": …, "error": null }`.
- **Memory** – every agent turn writes to both vector and graph stores before returning a response.
- **LangGraph** – single `CouncilState` TypedDict; nodes: `retrieve_memory → route_to_agent → ceo_node | coach_node → handoff_check → write_memory`.
- **Frontend** – vanilla JS modules in `static/js/`; dark/light theme via CSS variables on `:root`.

---

## 🚀 Getting Started

1. **Clone the repo** (if you haven’t already).  
2. **Copy the example environment file** and add your Anthropic API key:

   ```bash
   cp .env.example .env
   # Edit .env → set ANTHROPIC_API_KEY=sk-ant-...
   ```

3. **Create a virtual environment** and install dependencies:

   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Run the application**:

   ```bash
   python app.py
   # → http://localhost:8000
   ```

The UI will be served from `static/index.html` and the council endpoints are available under `/council/*`.

---

## 🔌 API Overview (prefix `/api/v1/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/council/chat` | POST | Send a message to the agent council; receives a streaming SSE response. |
| `/council/memory` | GET | Retrieve recent memory items for the council. |
| `/chat/*` | Various | General chat endpoints (non‑council). |
| `/memory/*` | Various | CRUD operations on raw memory (vector/graph). |
| `/agents/*` | Various | Agent‑specific endpoints (if needed). |

All successful responses follow `{ "data": …, "error": null }`. Errors return `{ "data": null, "error": "message" }`.

---

## 📈 Current Build Status (from CLAUDE.md)

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

*(Check the latest `CLAUDE.md` for updates.)*

---

## 🗺️ Roadmap

### Phase 1 – MVP (In Progress)
- CEO and Coach agents only.
- Hybrid memory layer (ChromaDB + Mem0).
- LangGraph orchestration with agent handoff.
- `/council` UI: agent selector, chat, memory sidebar, handoff indicator.

### Phase 2 – Future
- Add SEO and CFO agents.
- Launch Knowledge Marketplace (human‑coach content).
- Migrate from SQLite to Supabase + pgvector.
- Introduce full RBAC and advanced auth.

---

## 📄 License

Private – all rights reserved.

---

## 🙏 Acknowledgments

- Architectural inspiration from **Odysseus** (self‑hosted AI workspace) – same FastAPI pattern, ChromaDB setup, static frontend, with added `agents/` and `memory/` layers and LangGraph orchestration.
- Thanks to the Anthropic team for the Claude API.
- Open‑source dependencies listed in `requirements.txt`.

---

*Ready to outthink the competition? Start the council and let persistent memory give you the edge.*