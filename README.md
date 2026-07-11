# Edublox — AI-Powered Learning on Roblox

Upload any study PDF and play it as a personalized, Universe-themed Roblox
adventure. An LLM turns the material into a three-mission "Mission Plan"
(dialogue with an NPC tutor, an ordering puzzle, and an exploration scan),
and a persistent memory layer makes the experience smarter every session —
it remembers what each learner enjoys, struggles with, and has already
mastered.

Built for the **EverMind Challenge · Reinvented Education Hackathon**.

## How it works

```
study PDF ──▶ Web app ──▶ Backend ──▶ Mission Plan JSON ──▶ Roblox place
                             │  ▲
                     writes  ▼  │ recalls
                        EverOS memory
                 (profile + episodic, per learner)
```

1. **Upload** — the web app sends a PDF to the backend, which extracts its
   text (`pdfplumber`).
2. **Generate** — the backend recalls the learner's EverOS memory, then asks
   the LLM (via the Butterbase AI gateway) for a schema-validated Mission
   Plan: 3 learning objectives + 3 missions, personalized by memory.
3. **Play** — "Launch in Roblox" deep-links into the published place, which
   fetches the plan from `/api/config` and runs it: talk to the NPC (real
   LLM chat with correct-answer detection), solve the sequence puzzle
   (validated server-side), scan the exploration targets.
4. **Remember** — NPC chat turns and mission milestones are written back to
   EverOS, which distills them into a durable learner profile and episodic
   memory used by the next generation and chat.

## Repository layout

| Path | What it is | Owner |
|------|------------|-------|
| `backend/` | FastAPI server: upload, plan generation, NPC chat, reporting, EverOS adapter | Nori |
| `web/` | Next.js app: PDF upload, plan preview, Roblox launch | Steven |
| `roblox/` | Roblox place (Luau, Rojo): mission runtime + UI | Madi |
| `demo/` | Demo source PDF (solar system) for the scripted demo | — |
| `assets/` | Hackathon learner cards + EverOS loaders (preload weeks of history) | — |
| `storyline/` | Demo walkthrough and mission narrative docs | — |
| `PRD.md` | Full implementation spec | — |

Per-person task lists: `NORI.md`, `STEVEN.md`, `MADI.md`.

## Backend

FastAPI + Python. All routes under `/api`; canonical data contract in
[`backend/app/models/schemas.py`](backend/app/models/schemas.py).

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness: `{ "ok": true }` |
| `POST /api/upload` | PDF (≤25 MB) → `upload_id` + text preview |
| `POST /api/generate` | `upload_id` → validated Mission Plan (recalls learner memory first) |
| `GET /api/config?plan_id=...` | Plan + fresh `session_id` (Roblox calls on player join) |
| `POST /api/npc-chat` | In-character NPC reply + `is_correct_answer` signal |
| `POST /api/report` | Mission events; milestones + behavior signals written to EverOS as concept-level observations |
| `GET /api/report/{session_id}` | Session progress summary |
| `GET /api/memory/{learner_id}` | Memory reveal: what EverOS remembers (mastered / struggles / profile) — same recalls the generator sees |

### Persistence (Butterbase)

Butterbase is the app's backend twice over: its **AI gateway** serves every
LLM call, and its **database** (via the auto-generated data API) is the
durable copy of operational state — uploads, plans, sessions, and report
events — behind a write-through in-memory cache
([`storage.py`](backend/app/services/storage.py) +
[`butterbase_db.py`](backend/app/services/butterbase_db.py)). A backend
restart or redeploy no longer breaks live Roblox launch links or session
reports; if Butterbase is unreachable, the backend degrades gracefully to
in-memory-only. The division of labor with EverOS is deliberate:
**Butterbase stores what the app needs to run; EverOS remembers the
learner.**

### Run locally

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # then fill in keys (see below)
.venv/bin/uvicorn app.main:app --reload --port 8000
curl localhost:8000/health   # → {"ok":true}
```

A pre-built demo plan (`plan_id: demo_solar_system`) is seeded at startup,
so `/api/config?plan_id=demo_solar_system` always works — even with no
upload and no LLM key.

### Environment (`backend/.env`)

| Var | Notes |
|-----|-------|
| `BUTTERBASE_API_KEY` | Server-side only. The **only** LLM path — no credentials ever reach web or Roblox. |
| `BUTTERBASE_AI_BASE_URL` | App-scoped gateway URL: `https://api.butterbase.ai/v1/<app_id>` |
| `LLM_MODEL_LARGE` / `LLM_MODEL_SMALL` | Plan generation / NPC chat models |
| `EVEROS_API_KEY` | EverOS Cloud key ([get one](https://everos.evermind.ai/api-keys)). Optional: missing key degrades gracefully. |
| `EVEROS_BASE_URL` | `https://api.evermind.ai/api/v1` |
| `ALLOWED_ORIGIN` | Deployed web app origin (CORS) |
| `PUBLIC_BASE_URL` | This backend's public URL (Roblox `BackendClient.lua` needs it) |

### Web app (`web/.env.local`)

```
NEXT_PUBLIC_BACKEND_URL=<backend url>
NEXT_PUBLIC_ROBLOX_PLACE_ID=<published place id>
```

For Butterbase, set both variables in the frontend deployment **before**
building or redeploying. Next.js compiles `NEXT_PUBLIC_*` values into the
browser bundle, so changing them after uploading `web/out` does not update the
site. The backend URL must be public HTTPS (not `localhost`), and the backend's
`ALLOWED_ORIGIN` must exactly match the Butterbase frontend origin.

The static deployment opens plans through
`/preview/?plan_id=<plan id>`. Keeping the plan ID in the query string lets one
exported preview page handle newly generated plans without requiring a server
route for every ID.

```bash
cd web && npm install && npm run dev   # localhost:3000
```

## Memory (EverOS)

EverOS stores each Roblox game session's raw transcripts (NPC chat turns +
concept-level mission observations + engagement `behavior_signal`s) and
auto-extracts them into a learner **profile** (persistent traits) and
**episodic memory** (what happened). Three labeled recalls — *mastered*,
*struggles*, *profile* — run before plan generation, so plans visibly
progress session over session (mastered concepts aren't re-tested; the NPC's
opening line nods to last time), and the same recalls power the
"what the tutor remembers" reveal panel on the web preview page. The NPC
additionally sees the live session event feed, so it can react mid-session
to a just-failed puzzle or a distracted player. Writes happen off the
request path and are flushed so extraction completes; an EverOS outage
never blocks gameplay.

To start a demo with weeks of realistic history, preload a learner card:

```bash
export EVEROS_API_KEY=<your key>
backend/.venv/bin/python assets/load_learner.py assets/leo_carter.json
# Leo, 10 — loves space; great fit for the solar-system demo
backend/.venv/bin/python assets/load_learner.py assets/create.json
# Kai, 11 — presentation persona: skateboarder whose Roblox history shows
# gravity mastered; the seeded Newton's-laws demo plan builds on it
```

## Demo script

See [`storyline/DEMO-WALKTHROUGH.md`](storyline/DEMO-WALKTHROUGH.md).

**Presentation shortcut:** the web app's home page has a
"▶ Demo: Newton's Laws of Motion" button that jumps straight to the
pre-seeded `demo_newton_laws` plan (learner: Kai, from
`assets/create.json`) — no upload, no LLM call. The preview page's
"What the tutor remembers" panel shows Kai's recalled history: gravity and
planet order already mastered in his solar-system Roblox sessions, so the
Newton plan is the visible next step.

Full flow: upload a study PDF on the web app, preview the generated plan,
launch into Roblox, complete the three missions, then show the session
report — and on a second run, point out what the NPC already remembers.

The demo content is the solar system, but nothing is hardcoded to it: any
school-subject PDF flows through the same upload → generate → play pipeline.
