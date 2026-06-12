# Cannae — First Task Prompt
## Paste this into Claude Code to start the build

---

Read CLAUDE.md fully before doing anything. Confirm you understand the project by stating:
1. What Cannae is in one sentence
2. The MVP scope (what's in, what's deferred)
3. The current build status checklist

Then execute the following in order. Complete each step before moving to the next.
Do not skip steps. Do not add features not listed here.

---

## Step 1 — Project scaffold

Create the following files with minimal but correct content:

**requirements.txt**
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-dotenv==1.0.1
pydantic==2.7.1
pydantic-settings==2.2.1
sqlalchemy==2.0.30
anthropic==0.26.0
chromadb==0.5.0
mem0ai==0.0.91
langgraph==0.1.1
langchain-anthropic==0.1.15
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.27.0
```

**.env.example**
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
CHROMADB_PATH=./data/chroma
MEM0_API_KEY=your-mem0-key-here
DATABASE_URL=sqlite:///./data/cannae.db
JWT_SECRET=change-this-in-production
APP_HOST=127.0.0.1
APP_PORT=8000
DEBUG=true
```

**.gitignore**
- Standard Python gitignore
- Plus: .env, data/, *.db, __pycache__, .venv, venv

---

## Step 2 — Core layer

Create these files:

**core/constants.py**
- CLAUDE_MODEL = "claude-sonnet-4-20250514"
- MAX_TOKENS = 4096
- Agent name literals: CEO_AGENT = "ceo", COACH_AGENT = "coach"

**core/config.py**
- Pydantic BaseSettings class `Settings`
- Fields: anthropic_api_key, chromadb_path, mem0_api_key, database_url, jwt_secret, app_host, app_port, debug
- Singleton pattern: `get_settings()` cached with `@lru_cache`

**core/database.py**
- SQLAlchemy async engine from settings.database_url
- `get_db()` async dependency

---

## Step 3 — Memory layer

Create these three files in order:

**memory/vector_store.py**
- Class `VectorStore`
- Uses ChromaDB embedded client, path from settings
- Methods:
  - `async add(user_id: str, content: str, metadata: dict) -> str` (returns doc_id)
  - `async query(user_id: str, query: str, n_results: int = 5) -> list[dict]`
  - Collection name per user: `f"user_{user_id}"`

**memory/graph_memory.py**
- Class `GraphMemory`
- Wraps Mem0 `Memory` client (or stub it with a dict if Mem0 key not present — fail gracefully)
- Methods:
  - `async add_decision(user_id: str, content: str, agent_id: str) -> str`
  - `async get_context(user_id: str, query: str) -> list[dict]`

**memory/memory_layer.py**
- Class `MemoryLayer` — composes VectorStore + GraphMemory
- Methods:
  - `async write(user_id: str, content: str, agent_id: str, metadata: dict)`
    writes to both stores simultaneously (asyncio.gather)
  - `async read(user_id: str, query: str) -> dict`
    returns `{ "semantic": [...], "graph": [...] }` — merged results
- This is the ONLY interface agents should use — they never call vector_store or graph_memory directly

---

## Step 4 — CEO Agent (system prompt is priority)

**agents/base_agent.py**
- Abstract class `BaseAgent`
- Constructor: takes `memory_layer: MemoryLayer`, `settings: Settings`
- Abstract method: `async invoke(user_id: str, message: str, history: list) -> str`
- Shared method: `async _build_memory_context(user_id: str, query: str) -> str`
  — calls memory_layer.read() and formats results as a context block for injection

**agents/ceo_agent.py**
- Class `CEOAgent(BaseAgent)`
- Write a detailed CEO_SYSTEM_PROMPT string. It must include:
  - Role: strategic advisor with full memory of the user's past decisions
  - The Cannae philosophy (Hannibal — outthink through superior preparation and memory)
  - Explicit instruction to reference past decisions from memory context when relevant
  - Tone: direct, confident, systems-thinker — no filler, no hedging
  - Signature rule: every response ends with "**Next highest-leverage action:**"
  - Instruction: if a decision should trigger an accountability plan, end with "[HANDOFF→COACH]"
- `async invoke(user_id, message, history)`:
  1. Pull memory context via _build_memory_context()
  2. Inject into system prompt
  3. Call Anthropic API with full history
  4. Write interaction to memory_layer
  5. Return response text

---

## Step 5 — Quick smoke test

Create a file `test_ceo.py` at root level (not a pytest file — just a runnable script):

```python
import asyncio
from core.config import get_settings
from memory.memory_layer import MemoryLayer
from agents.ceo_agent import CEOAgent

async def main():
    settings = get_settings()
    memory = MemoryLayer(settings)
    ceo = CEOAgent(memory, settings)

    response = await ceo.invoke(
        user_id="test_user_001",
        message="We're deciding between raising a $500K seed round now vs staying bootstrapped for 12 more months. Revenue is $8K MRR, growing 15% month over month. What's your read?",
        history=[]
    )
    print("\n--- CEO RESPONSE ---\n")
    print(response)

asyncio.run(main())
```

Run it. The CEO should respond in character. If it works, we move to the Coach agent and LangGraph.

---

## Done when:

- [ ] All files from Steps 1-4 exist and are syntactically valid
- [ ] `python test_ceo.py` runs without errors
- [ ] CEO responds in character (strategic, references Cannae philosophy, ends with next action)
- [ ] Memory write completes without error (even if ChromaDB/Mem0 use local stubs)

Report back with the test output and any errors.
