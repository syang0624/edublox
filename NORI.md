# Nori — Backend (FastAPI + Python)

## Ownership

Everything under `backend/` and `demo/`. The API server, PDF extraction, LLM-powered plan generation, NPC chat, EverOS memory integration, and data models.

## Files You Own

```
backend/
├── app/
│   ├── main.py                         # FastAPI app, CORS, router includes, demo plan seeding
│   ├── config.py                       # Environment variable settings
│   ├── routes/
│   │   ├── upload.py                   # POST /api/upload
│   │   ├── generate.py                 # POST /api/generate
│   │   ├── config.py                   # GET /api/config?plan_id=...
│   │   ├── npc_chat.py                 # POST /api/npc-chat
│   │   └── report.py                   # POST /api/report + GET /api/report/{session_id}
│   ├── services/
│   │   ├── pdf_extractor.py            # pdfplumber text extraction
│   │   ├── llm.py                      # Butterbase AI gateway client (OpenAI-compatible)
│   │   ├── plan_generator.py           # System prompt + JSON parsing + validation
│   │   ├── npc_chat_service.py         # NPC persona + correct-answer detection
│   │   ├── everos_memory.py            # Durable learner memory (recall + write)
│   │   └── storage.py                  # In-memory dicts for uploads/plans/sessions
│   ├── models/
│   │   └── schemas.py                  # Pydantic models (canonical data contract)
│   └── demo/
│       └── solar_system_plan.json      # Pre-built demo Mission Plan (plan_id: "demo_solar_system")
├── requirements.txt
└── .env

demo/
└── solar_system.pdf                    # Demo source PDF for scripted demo
```

## Task Checklist

### Setup
- [ ] Initialize Python project in `backend/`
- [ ] Create `requirements.txt` — PRD 4.12: fastapi, uvicorn, pydantic, python-multipart, pdfplumber, openai, httpx, python-dotenv
- [ ] Create `.env` with all env vars — PRD section 2
- [ ] Create `app/config.py` — PRD 4.13

### Data Models
- [ ] **`models/schemas.py`** — PRD section 3
  - `MissionType` enum, `DialogueMission`, `PuzzleMission`, `ExplorationMission`
  - `MissionPlan`, `UploadResponse`, `GenerateRequest`, `GenerateResponse`
  - `ConfigResponse`, `NpcChatRequest`, `NpcChatResponse`, `ReportEvent`

### Core Services
- [ ] **`services/storage.py`** — PRD 4.2: in-memory dicts for uploads, plans, sessions, events
- [ ] **`services/pdf_extractor.py`** — PRD 4.4: extract text from PDF bytes via pdfplumber
- [ ] **`services/llm.py`** — PRD 4.5: OpenAI client pointing at Butterbase AI gateway
- [ ] **`services/plan_generator.py`** — PRD 4.6: system prompt, JSON generation, validation
  - Must validate: 3 objectives, 3 missions (one of each type), valid locations, valid exploration targets
  - Strip markdown fences from LLM output before parsing
- [ ] **`services/npc_chat_service.py`** — PRD 4.10: roleplay prompt, correct-answer detection via JSON response
- [ ] **`services/everos_memory.py`** — PRD 4.2a: recall (hybrid search) + async remember_turns

### Routes
- [ ] **`routes/upload.py`** — PRD 4.3: accept PDF, validate size/type, extract text, truncate to 15k chars
- [ ] **`routes/generate.py`** — PRD 4.7: recall learner memory, generate plan, save to storage
- [ ] **`routes/config.py`** — PRD 4.8: return plan + new session_id by plan_id query param
- [ ] **`routes/npc_chat.py`** — PRD 4.9: proxy to npc_chat_service
- [ ] **`routes/report.py`** — PRD 4.11: log events, write milestones to EverOS, GET report by session

### App Entry
- [ ] **`main.py`** — PRD 4.1
  - FastAPI app with CORS middleware
  - Include all routers under `/api`
  - `/health` endpoint
  - On startup: seed demo solar system plan from `demo/solar_system_plan.json` (plan_id: `demo_solar_system`) — PRD 4.15

### Demo Content
- [ ] Create `demo/solar_system_plan.json` — PRD 4.15 (exact JSON provided in PRD)
- [ ] Place or source `demo/solar_system.pdf` for the scripted demo

### Deployment
- [ ] Deploy via Railway or Render
- [ ] Set all env vars on hosting platform
- [ ] Confirm `/health` returns `{ ok: true }`
- [ ] Confirm Butterbase AI gateway works with one test completion

## Integration Points

| What | Who to coordinate with |
|------|----------------------|
| API request/response shapes (schemas.py) | **Steven** — web app calls `/api/upload`, `/api/generate`, `/api/config` |
| `/api/config?plan_id=...` endpoint | **Madi** — Roblox calls this on player join |
| `/api/npc-chat` endpoint | **Madi** — Roblox proxies player chat through this |
| `/api/report` endpoint | **Madi** — Roblox posts mission events here |
| `PUBLIC_BASE_URL` | **Madi** — needs this for `BackendClient.lua` BASE url |
| EverOS API key + setup | Shared — create Cloud API key, verify write + search |

## Acceptance Criteria

1. `/health` returns `{ ok: true }`
2. `POST /api/upload` accepts PDF (max 25 MB), returns `upload_id` + 500-char preview
3. `POST /api/generate` produces a valid, schema-conformant Mission Plan JSON with 3 objectives and 3 missions (one dialogue, one puzzle, one exploration)
4. Works for **any subject PDF** — not just solar system
5. `GET /api/config?plan_id=...` returns plan + session_id; demo plan (`demo_solar_system`) is always available
6. `POST /api/npc-chat` returns in-character NPC reply with `is_correct_answer` signal
7. NPC never reveals the answer directly; gives hints after 2+ wrong attempts
8. EverOS memory is recalled before generation and NPC chat; turns are written after interactions
9. EverOS failure degrades gracefully — logged warning, no crash
10. Puzzle validation is server-side only (correct_order check)
11. Butterbase is the only LLM path; no credentials exposed to web or Roblox
