# PRD — AI Learning Worlds on Roblox

**Implementation spec. Written so an AI coding agent can build this end-to-end in one pass.**

---

## 0. What we're building

A three-part system:

1. **Web app** (Next.js) — user uploads a PDF, previews a generated mission plan, clicks "Launch in Roblox"
2. **Backend** (FastAPI, Python) — extracts PDF text, calls an LLM to generate a Mission Plan JSON, serves that JSON to Roblox at play time, and handles NPC chat turns
3. **Roblox place** (Luau) — one published place with a pre-built Ancient Egypt scene that loads a Mission Plan from the backend and executes it as playable content

**Demo topic is Ancient Egypt only. Do not try to generalize.**

---

## 1. Repository layout

```
learning-worlds/
├── web/                          # Next.js app
│   ├── app/
│   │   ├── page.tsx              # Upload page
│   │   ├── preview/[planId]/page.tsx  # Mission Plan preview + launch
│   │   ├── api/
│   │   │   └── proxy/[...path]/route.ts   # Proxies to backend (optional, for CORS)
│   ├── components/
│   │   ├── UploadDropzone.tsx
│   │   ├── GenerationProgress.tsx
│   │   └── MissionPlanPreview.tsx
│   ├── lib/
│   │   └── api.ts                # fetch wrappers
│   ├── package.json
│   └── .env.local                # NEXT_PUBLIC_BACKEND_URL, NEXT_PUBLIC_ROBLOX_PLACE_ID
│
├── backend/                      # FastAPI
│   ├── app/
│   │   ├── main.py               # FastAPI app + routes
│   │   ├── routes/
│   │   │   ├── upload.py
│   │   │   ├── generate.py
│   │   │   ├── config.py
│   │   │   ├── npc_chat.py
│   │   │   └── report.py
│   │   ├── services/
│   │   │   ├── pdf_extractor.py
│   │   │   ├── llm.py            # LLM client wrapper
│   │   │   ├── plan_generator.py # Prompts + JSON parsing
│   │   │   ├── npc_chat_service.py
│   │   │   └── storage.py        # In-memory store (dict); no DB for hackathon
│   │   ├── models/
│   │   │   └── schemas.py        # Pydantic models
│   │   └── config.py             # env vars
│   ├── requirements.txt
│   └── .env
│
└── roblox/                       # Roblox Studio project (Rojo-compatible)
    ├── src/
    │   ├── ServerScriptService/
    │   │   ├── MissionRouter.server.lua
    │   │   └── BackendClient.lua         # ModuleScript
    │   ├── StarterPlayerScripts/
    │   │   └── ClientBootstrap.client.lua
    │   ├── ReplicatedStorage/
    │   │   ├── MissionModules/
    │   │   │   ├── DialogueMission.lua
    │   │   │   ├── PuzzleMission.lua
    │   │   │   └── ExplorationMission.lua
    │   │   ├── UI/
    │   │   │   ├── DialogueUI.lua
    │   │   │   ├── PuzzleUI.lua
    │   │   │   └── HUD.lua
    │   │   └── Remotes.lua               # RemoteEvents/Functions setup
    │   └── Workspace/
    │       └── (built scene: pyramid entrance, burial chamber, Nile valley)
    └── default.project.json      # Rojo config
```

---

## 2. Environment variables

### `backend/.env`

```
LLM_PROVIDER=anthropic            # or "openai"
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...             # only if using openai
LLM_MODEL_LARGE=claude-sonnet-4-5-20250929   # for plan generation
LLM_MODEL_SMALL=claude-haiku-4-5-20251001    # for NPC chat
TOKEN_SECRET=any-random-string-32-chars-min
ALLOWED_ORIGIN=https://your-web-app.vercel.app
PUBLIC_BASE_URL=https://your-backend.up.railway.app
```

### `web/.env.local`

```
NEXT_PUBLIC_BACKEND_URL=https://your-backend.up.railway.app
NEXT_PUBLIC_ROBLOX_PLACE_ID=1234567890
```

---

## 3. Data model (Pydantic + JSON contract)

This is the canonical shape. Web, backend, and Roblox all speak this.

```python
# backend/app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from enum import Enum

class MissionType(str, Enum):
    DIALOGUE = "dialogue"
    PUZZLE = "puzzle"
    EXPLORATION = "exploration"

class DialogueMission(BaseModel):
    type: Literal["dialogue"] = "dialogue"
    mission_id: str
    location: Literal["pyramid_entrance", "burial_chamber", "nile_valley"]
    npc_name: str                       # e.g., "Imhotep"
    npc_persona: str                    # 1-2 sentences, in-character behavior brief
    opening_line: str                   # what NPC says when player approaches
    required_question: str              # the question player must correctly answer
    correct_answer_hints: List[str]     # 3-5 keywords/phrases judged as correct
    success_line: str                   # NPC line on correct answer
    max_attempts: int = 3

class PuzzleMission(BaseModel):
    type: Literal["puzzle"] = "puzzle"
    mission_id: str
    location: Literal["pyramid_entrance", "burial_chamber", "nile_valley"]
    prompt: str                         # "Order the mummification steps"
    items: List[str]                    # display strings, presented shuffled
    correct_order: List[int]            # indices into items in the correct order

class ExplorationMission(BaseModel):
    type: Literal["exploration"] = "exploration"
    mission_id: str
    location: Literal["pyramid_entrance", "burial_chamber", "nile_valley"]
    prompt: str                         # "Find 3 things the Nile provided"
    targets: List[str]                  # object tags in the scene
    hint: Optional[str] = None

Mission = DialogueMission | PuzzleMission | ExplorationMission

class MissionPlan(BaseModel):
    plan_id: str
    title: str                          # "Secrets of the Old Kingdom"
    topic: str = "Ancient Egypt"
    objectives: List[str]               # 3 short learning objectives
    missions: List[Mission]             # exactly 3 missions, one of each type is ideal

class UploadResponse(BaseModel):
    upload_id: str
    extracted_text_preview: str         # first 500 chars for user confirmation
    char_count: int

class GenerateRequest(BaseModel):
    upload_id: str

class GenerateResponse(BaseModel):
    plan_id: str
    plan: MissionPlan

class ConfigResponse(BaseModel):
    plan: MissionPlan
    session_id: str                     # unique per launch, used for reporting

class NpcChatRequest(BaseModel):
    session_id: str
    mission_id: str
    npc_name: str
    npc_persona: str
    topic: str
    player_message: str
    conversation_history: List[dict] = []  # [{"role": "player"|"npc", "content": "..."}]

class NpcChatResponse(BaseModel):
    npc_reply: str
    is_correct_answer: bool             # true if this reply corresponds to a correct answer to required_question

class ReportEvent(BaseModel):
    session_id: str
    mission_id: str
    event_type: Literal["mission_started", "mission_completed", "mission_failed", "answer_submitted"]
    payload: dict = {}
```

---

## 4. Backend implementation

### 4.1 `main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import upload, generate, config, npc_chat, report

app = FastAPI(title="Learning Worlds API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGIN, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(generate.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(npc_chat.router, prefix="/api")
app.include_router(report.router, prefix="/api")

@app.get("/health")
def health():
    return {"ok": True}
```

### 4.2 `services/storage.py`

Hackathon uses in-memory dicts. **Not thread-safe for real use**, fine for demo.

```python
# app/services/storage.py
from typing import Dict
from app.models.schemas import MissionPlan

_uploads: Dict[str, str] = {}       # upload_id -> extracted_text
_plans: Dict[str, MissionPlan] = {} # plan_id -> MissionPlan
_sessions: Dict[str, str] = {}      # session_id -> plan_id
_events: list = []                  # list of ReportEvent

def save_upload(upload_id: str, text: str): _uploads[upload_id] = text
def get_upload(upload_id: str) -> str: return _uploads[upload_id]

def save_plan(plan: MissionPlan): _plans[plan.plan_id] = plan
def get_plan(plan_id: str) -> MissionPlan: return _plans[plan_id]

def create_session(plan_id: str) -> str:
    import uuid
    sid = uuid.uuid4().hex
    _sessions[sid] = plan_id
    return sid

def get_session_plan(session_id: str) -> MissionPlan:
    plan_id = _sessions[session_id]
    return _plans[plan_id]

def append_event(event): _events.append(event)
def events_for_session(session_id: str):
    return [e for e in _events if e.session_id == session_id]
```

### 4.3 `routes/upload.py`

```python
# app/routes/upload.py
import uuid
from fastapi import APIRouter, UploadFile, HTTPException
from app.services import pdf_extractor, storage
from app.models.schemas import UploadResponse

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")
    contents = await file.read()
    if len(contents) > 25 * 1024 * 1024:
        raise HTTPException(400, "File exceeds 25MB")
    text = pdf_extractor.extract_text(contents)
    if len(text.strip()) < 100:
        raise HTTPException(400, "Could not extract meaningful text from PDF")
    # Truncate to keep LLM cost down
    text = text[:15000]
    upload_id = uuid.uuid4().hex
    storage.save_upload(upload_id, text)
    return UploadResponse(
        upload_id=upload_id,
        extracted_text_preview=text[:500],
        char_count=len(text),
    )
```

### 4.4 `services/pdf_extractor.py`

```python
# app/services/pdf_extractor.py
import io
import pdfplumber

def extract_text(pdf_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            text_parts.append(t)
    return "\n\n".join(text_parts)
```

### 4.5 `services/llm.py`

Abstract over provider. Return raw text; caller parses JSON.

```python
# app/services/llm.py
from app.config import settings

def complete(system: str, user: str, model: str, max_tokens: int = 2000) -> str:
    if settings.LLM_PROVIDER == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text
    elif settings.LLM_PROVIDER == "openai":
        import openai
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content
    else:
        raise RuntimeError(f"Unknown provider: {settings.LLM_PROVIDER}")
```

### 4.6 `services/plan_generator.py`

**This is the highest-leverage file. Get the prompt right.**

````python
# app/services/plan_generator.py
import json
import uuid
from app.services import llm
from app.config import settings
from app.models.schemas import MissionPlan

SYSTEM_PROMPT = """You are a curriculum designer generating game missions for a Roblox learning experience aimed at kids aged 9-12.

You will be given source study material (a textbook chapter or similar) about Ancient Egypt.
You must output a Mission Plan as strict JSON.

The Mission Plan contains:
- title: A punchy, adventurous name for the experience (max 8 words).
- topic: Always "Ancient Egypt" for now.
- objectives: Exactly 3 learning objectives phrased as things a student should be able to DO ("Explain...", "Identify...", "Describe..."). Base them on the source material.
- missions: Exactly 3 missions, one of each type: "dialogue", "puzzle", "exploration". Present them in that order.

Each mission uses one of three locations: "pyramid_entrance", "burial_chamber", "nile_valley". Pick the location that best fits the mission's content.

Mission type rules:

DIALOGUE mission:
- npc_name: A real historical Egyptian figure appropriate to the material (Imhotep, Cleopatra, Ramses II, Hatshepsut, a scribe named Ankh, etc.)
- npc_persona: 1-2 sentences describing how they speak and what they know. Must stay in scope (only knowledge from the source material).
- opening_line: What the NPC says when the player approaches. In-character, curious, sets up the required_question.
- required_question: A question that tests one specific fact/concept from the material.
- correct_answer_hints: 3-5 short keywords/phrases that indicate the player answered correctly. These are used for fuzzy matching.
- success_line: NPC's in-character response when the player answers correctly.
- max_attempts: 3

PUZZLE mission:
- prompt: A one-sentence instruction ("Order the steps of mummification.").
- items: 3-6 display strings that must be ordered.
- correct_order: Array of indices into items showing the correct sequence.

EXPLORATION mission:
- prompt: A one-sentence instruction ("Find 3 gifts of the Nile.").
- targets: Array of 3 lowercase snake_case tags. Choose from this whitelist ONLY: "water", "fertile_soil", "papyrus", "fish", "reeds", "clay", "gold", "limestone", "wheat", "flax", "cattle", "birds". Pick 3 that best match the material.
- hint: One short sentence to help the player.

Rules for the whole plan:
1. All content must be answerable from the source material. Do not add facts not in the material.
2. If the material only covers part of Ancient Egypt (e.g., just pyramids), the missions should reflect that scope, not general Egyptian history.
3. Language must be appropriate for ages 9-12.
4. Do not invent NPCs, items, or targets not in the whitelist.
5. Output ONLY the JSON object. No markdown fences, no commentary, no preamble.

The JSON must match this exact schema:

{
  "title": "string",
  "topic": "Ancient Egypt",
  "objectives": ["string", "string", "string"],
  "missions": [
    {
      "type": "dialogue",
      "mission_id": "m1",
      "location": "pyramid_entrance" | "burial_chamber" | "nile_valley",
      "npc_name": "string",
      "npc_persona": "string",
      "opening_line": "string",
      "required_question": "string",
      "correct_answer_hints": ["string", "string", "string"],
      "success_line": "string",
      "max_attempts": 3
    },
    {
      "type": "puzzle",
      "mission_id": "m2",
      "location": "pyramid_entrance" | "burial_chamber" | "nile_valley",
      "prompt": "string",
      "items": ["string", "string", "string"],
      "correct_order": [0, 1, 2]
    },
    {
      "type": "exploration",
      "mission_id": "m3",
      "location": "pyramid_entrance" | "burial_chamber" | "nile_valley",
      "prompt": "string",
      "targets": ["water", "fertile_soil", "papyrus"],
      "hint": "string"
    }
  ]
}
"""

def generate_plan(source_text: str) -> MissionPlan:
    user = f"SOURCE MATERIAL:\n\n{source_text}\n\nNow output the Mission Plan JSON."
    raw = llm.complete(
        system=SYSTEM_PROMPT,
        user=user,
        model=settings.LLM_MODEL_LARGE,
        max_tokens=2500,
    )
    raw = _strip_json_fences(raw)
    data = json.loads(raw)
    data["plan_id"] = uuid.uuid4().hex
    plan = MissionPlan(**data)
    _validate_plan(plan)
    return plan

def _strip_json_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        # Strip ```json ... ``` or ``` ... ```
        s = s.split("\n", 1)[1] if "\n" in s else s
        if s.endswith("```"):
            s = s[: -3]
    return s.strip()

VALID_LOCATIONS = {"pyramid_entrance", "burial_chamber", "nile_valley"}
VALID_TARGETS = {"water", "fertile_soil", "papyrus", "fish", "reeds", "clay",
                 "gold", "limestone", "wheat", "flax", "cattle", "birds"}

def _validate_plan(plan: MissionPlan):
    assert len(plan.objectives) == 3, "Must have 3 objectives"
    assert len(plan.missions) == 3, "Must have 3 missions"
    types = [m.type for m in plan.missions]
    assert set(types) == {"dialogue", "puzzle", "exploration"}, f"Wrong mission types: {types}"
    for m in plan.missions:
        assert m.location in VALID_LOCATIONS
        if m.type == "exploration":
            for t in m.targets:
                assert t in VALID_TARGETS, f"Invalid target: {t}"
        if m.type == "puzzle":
            assert sorted(m.correct_order) == list(range(len(m.items))), \
                "correct_order must be a permutation of item indices"
````

### 4.7 `routes/generate.py`

```python
# app/routes/generate.py
from fastapi import APIRouter, HTTPException
from app.models.schemas import GenerateRequest, GenerateResponse
from app.services import storage, plan_generator

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    try:
        text = storage.get_upload(req.upload_id)
    except KeyError:
        raise HTTPException(404, "upload_id not found")
    try:
        plan = plan_generator.generate_plan(text)
    except Exception as e:
        raise HTTPException(500, f"Generation failed: {e}")
    storage.save_plan(plan)
    return GenerateResponse(plan_id=plan.plan_id, plan=plan)
```

### 4.8 `routes/config.py`

Roblox hits this on player join. **Return plan by `plan_id` (query param) — no auth for hackathon.**

```python
# app/routes/config.py
from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import ConfigResponse
from app.services import storage

router = APIRouter()

@router.get("/config", response_model=ConfigResponse)
def get_config(plan_id: str = Query(...)):
    try:
        plan = storage.get_plan(plan_id)
    except KeyError:
        raise HTTPException(404, "plan_id not found")
    session_id = storage.create_session(plan_id)
    return ConfigResponse(plan=plan, session_id=session_id)
```

### 4.9 `routes/npc_chat.py`

```python
# app/routes/npc_chat.py
from fastapi import APIRouter
from app.models.schemas import NpcChatRequest, NpcChatResponse
from app.services import npc_chat_service

router = APIRouter()

@router.post("/npc-chat", response_model=NpcChatResponse)
def npc_chat(req: NpcChatRequest):
    return npc_chat_service.reply(req)
```

### 4.10 `services/npc_chat_service.py`

````python
# app/services/npc_chat_service.py
import json
from app.services import llm, storage
from app.config import settings
from app.models.schemas import NpcChatRequest, NpcChatResponse

def _build_system(req: NpcChatRequest, required_question: str, hints: list[str]) -> str:
    return f"""You are roleplaying as {req.npc_name}, an NPC in a Roblox learning game about {req.topic}.

Persona: {req.npc_persona}

The player must eventually answer this question correctly: "{required_question}"
An answer is considered correct if it meaningfully covers any of these ideas: {", ".join(hints)}.

Rules:
- Stay in character.
- Keep replies short: 1-3 sentences, max 40 words.
- If the player asks something off-topic, gently steer back to the question.
- Do NOT reveal the answer directly. You may give a small hint if they seem stuck (after 2+ attempts).
- If the player's LAST message correctly answers the question, respond with the success line and end with the exact token [CORRECT] on a new line at the end.
- If it does not, keep the conversation going without [CORRECT].

Respond in JSON: {{"reply": "<your in-character reply>", "correct": true|false}}
"""

def reply(req: NpcChatRequest) -> NpcChatResponse:
    # Pull mission context to know required_question & hints
    # session_id maps to plan; find the mission by mission_id
    plan = storage.get_session_plan(req.session_id)
    mission = next(m for m in plan.missions if m.mission_id == req.mission_id)
    system = _build_system(req, mission.required_question, mission.correct_answer_hints)

    convo = "\n".join(
        f"{turn['role'].upper()}: {turn['content']}" for turn in req.conversation_history
    )
    user = f"{convo}\nPLAYER: {req.player_message}\n\nRespond as JSON."

    raw = llm.complete(system=system, user=user,
                       model=settings.LLM_MODEL_SMALL, max_tokens=200)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        data = json.loads(raw)
        return NpcChatResponse(npc_reply=data["reply"], is_correct_answer=bool(data.get("correct", False)))
    except Exception:
        # Fallback: treat as plain text, not correct
        return NpcChatResponse(npc_reply=raw[:200], is_correct_answer=False)
````

### 4.11 `routes/report.py`

```python
# app/routes/report.py
from fastapi import APIRouter
from app.models.schemas import ReportEvent
from app.services import storage

router = APIRouter()

@router.post("/report")
def report(event: ReportEvent):
    storage.append_event(event)
    return {"ok": True}

@router.get("/report/{session_id}")
def get_report(session_id: str):
    events = storage.events_for_session(session_id)
    completed = [e for e in events if e.event_type == "mission_completed"]
    return {
        "session_id": session_id,
        "missions_completed": len(completed),
        "events": [e.dict() for e in events],
    }
```

### 4.12 `requirements.txt`

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
python-multipart==0.0.9
pdfplumber==0.11.4
anthropic==0.39.0
openai==1.51.0
python-dotenv==1.0.1
```

### 4.13 `config.py`

```python
# app/config.py
import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL_LARGE = os.getenv("LLM_MODEL_LARGE", "claude-sonnet-4-5-20250929")
    LLM_MODEL_SMALL = os.getenv("LLM_MODEL_SMALL", "claude-haiku-4-5-20251001")
    ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")
    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")

settings = Settings()
```

### 4.14 Run locally

```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

---

## 5. Web app implementation

### 5.1 `web/lib/api.ts`

```ts
const BASE = process.env.NEXT_PUBLIC_BACKEND_URL!;

export async function uploadPdf(file: File) {
    const fd = new FormData();
    fd.append("file", file);
    const r = await fetch(`${BASE}/api/upload`, { method: "POST", body: fd });
    if (!r.ok) throw new Error(await r.text());
    return r.json() as Promise<{
        upload_id: string;
        extracted_text_preview: string;
        char_count: number;
    }>;
}

export async function generatePlan(uploadId: string) {
    const r = await fetch(`${BASE}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ upload_id: uploadId }),
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json() as Promise<{ plan_id: string; plan: any }>;
}
```

### 5.2 `web/app/page.tsx` — upload flow

```tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { uploadPdf, generatePlan } from "@/lib/api";

export default function Home() {
    const router = useRouter();
    const [status, setStatus] = useState<
        "idle" | "uploading" | "generating" | "error"
    >("idle");
    const [error, setError] = useState<string>("");

    async function handleFile(file: File) {
        try {
            setStatus("uploading");
            const { upload_id } = await uploadPdf(file);
            setStatus("generating");
            const { plan_id } = await generatePlan(upload_id);
            router.push(`/preview/${plan_id}`);
        } catch (e: any) {
            setStatus("error");
            setError(e.message || "Something went wrong");
        }
    }

    return (
        <main className="min-h-screen flex items-center justify-center p-8 bg-amber-50">
            <div className="max-w-xl w-full text-center">
                <h1 className="text-4xl font-bold mb-2">Learning Worlds</h1>
                <p className="text-neutral-600 mb-8">
                    Upload a study PDF. We'll turn it into a Roblox adventure.
                </p>

                {status === "idle" && (
                    <label className="block border-2 border-dashed border-amber-400 rounded-xl p-12 cursor-pointer hover:bg-amber-100 transition">
                        <input
                            type="file"
                            accept="application/pdf"
                            className="hidden"
                            onChange={(e) =>
                                e.target.files?.[0] &&
                                handleFile(e.target.files[0])
                            }
                        />
                        <div className="text-lg">
                            Drop your PDF here, or click to browse
                        </div>
                        <div className="text-sm text-neutral-500 mt-2">
                            Max 25MB · Ancient Egypt topics work best
                        </div>
                    </label>
                )}

                {status === "uploading" && (
                    <Progress label="Reading your material..." />
                )}
                {status === "generating" && (
                    <Progress label="Designing your world..." />
                )}
                {status === "error" && (
                    <div className="text-red-600">
                        {error}
                        <button
                            className="block mx-auto mt-4 underline"
                            onClick={() => setStatus("idle")}
                        >
                            Try again
                        </button>
                    </div>
                )}
            </div>
        </main>
    );
}

function Progress({ label }: { label: string }) {
    return (
        <div className="p-8">
            <div className="animate-pulse text-xl">{label}</div>
            <div className="text-sm text-neutral-500 mt-2">
                This can take up to 90 seconds
            </div>
        </div>
    );
}
```

### 5.3 `web/app/preview/[planId]/page.tsx`

```tsx
"use client";
import { useEffect, useState } from "react";

export default function Preview({ params }: { params: { planId: string } }) {
    const [plan, setPlan] = useState<any>(null);
    const placeId = process.env.NEXT_PUBLIC_ROBLOX_PLACE_ID;

    useEffect(() => {
        fetch(
            `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/config?plan_id=${params.planId}`,
        )
            .then((r) => r.json())
            .then((d) => setPlan(d.plan));
    }, [params.planId]);

    if (!plan) return <div className="p-8">Loading...</div>;

    // Deep link. launchData carries the plan_id so the Roblox place fetches its own config.
    const launchData = encodeURIComponent(
        JSON.stringify({ plan_id: params.planId }),
    );
    const launchUrl = `https://www.roblox.com/games/start?placeId=${placeId}&launchData=${launchData}`;

    return (
        <main className="min-h-screen p-8 bg-amber-50">
            <div className="max-w-2xl mx-auto">
                <h1 className="text-3xl font-bold">{plan.title}</h1>
                <p className="text-neutral-600 mt-1">{plan.topic}</p>

                <section className="mt-8">
                    <h2 className="text-xl font-semibold mb-2">
                        You will learn to:
                    </h2>
                    <ul className="list-disc pl-6 space-y-1">
                        {plan.objectives.map((o: string, i: number) => (
                            <li key={i}>{o}</li>
                        ))}
                    </ul>
                </section>

                <section className="mt-8">
                    <h2 className="text-xl font-semibold mb-2">Missions:</h2>
                    <ol className="space-y-3">
                        {plan.missions.map((m: any) => (
                            <li
                                key={m.mission_id}
                                className="p-4 bg-white rounded-lg shadow-sm"
                            >
                                <div className="text-sm uppercase text-amber-700">
                                    {m.type}
                                </div>
                                <div className="font-medium">
                                    {m.type === "dialogue" &&
                                        `Speak with ${m.npc_name}`}
                                    {m.type === "puzzle" && m.prompt}
                                    {m.type === "exploration" && m.prompt}
                                </div>
                                <div className="text-sm text-neutral-500">
                                    Location: {m.location.replace("_", " ")}
                                </div>
                            </li>
                        ))}
                    </ol>
                </section>

                <a
                    href={launchUrl}
                    className="mt-8 block text-center bg-amber-600 hover:bg-amber-700 text-white text-xl font-semibold py-4 rounded-xl"
                >
                    Launch in Roblox
                </a>
            </div>
        </main>
    );
}
```

### 5.4 Web `package.json` deps

```
next, react, react-dom, typescript, tailwindcss
```

---

## 6. Roblox implementation

### 6.1 Studio setup checklist (do first)

1. Create a new Roblox place. **Publish it.**
2. Game Settings → Security → **Allow HTTP Requests: ON**.
3. Game Settings → Options → **Enable Studio Access to API Services: ON**.
4. Grab the Place ID from the URL. Put it in `web/.env.local` as `NEXT_PUBLIC_ROBLOX_PLACE_ID`.
5. Build the three-zone scene:
    - **pyramid_entrance:** a large flat sandy area with a Part-built pyramid shape, an NPC spawn point named `NPC_Spawn`, and a `Zone_Trigger` Part.
    - **burial_chamber:** a walled indoor room. Include a `PuzzleTable` Part where the puzzle UI anchors.
    - **nile_valley:** a green riverbank area with 6+ Parts tagged (via CollectionService) with target strings: `water`, `fertile_soil`, `papyrus`, `fish`, `reeds`, `clay`, `wheat`, `flax`, `cattle`, `birds`, `gold`, `limestone`. Spread them around.
6. Each location has a teleport SpawnLocation named `Spawn_pyramid_entrance` etc.

### 6.2 `ReplicatedStorage/Remotes.lua`

```lua
-- ModuleScript
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Remotes = {}

local folder = ReplicatedStorage:FindFirstChild("Remotes") or Instance.new("Folder", ReplicatedStorage)
folder.Name = "Remotes"

local function ensureRemote(name, className)
  local r = folder:FindFirstChild(name)
  if not r then
    r = Instance.new(className, folder)
    r.Name = name
  end
  return r
end

Remotes.LoadPlan       = ensureRemote("LoadPlan",       "RemoteEvent")   -- server -> client, sends plan
Remotes.StartMission   = ensureRemote("StartMission",   "RemoteEvent")   -- server -> client
Remotes.MissionResult  = ensureRemote("MissionResult",  "RemoteEvent")   -- client -> server
Remotes.NpcChat        = ensureRemote("NpcChat",        "RemoteFunction")-- client -> server -> backend
Remotes.SubmitPuzzle   = ensureRemote("SubmitPuzzle",   "RemoteFunction")
Remotes.CollectTarget  = ensureRemote("CollectTarget",  "RemoteEvent")

return Remotes
```

### 6.3 `ServerScriptService/BackendClient.lua`

```lua
-- ModuleScript
local HttpService = game:GetService("HttpService")

local BackendClient = {}

-- HARDCODE for hackathon. Move to a secret store later.
local BASE = "https://your-backend.up.railway.app"

function BackendClient:getConfig(planId)
  local url = BASE .. "/api/config?plan_id=" .. planId
  local ok, resp = pcall(function()
    return HttpService:GetAsync(url, false)
  end)
  if not ok then warn("getConfig failed: " .. tostring(resp)); return nil end
  return HttpService:JSONDecode(resp)
end

function BackendClient:npcChat(payload)
  local url = BASE .. "/api/npc-chat"
  local ok, resp = pcall(function()
    return HttpService:PostAsync(url, HttpService:JSONEncode(payload), Enum.HttpContentType.ApplicationJson)
  end)
  if not ok then warn("npcChat failed: " .. tostring(resp)); return nil end
  return HttpService:JSONDecode(resp)
end

function BackendClient:report(event)
  local url = BASE .. "/api/report"
  pcall(function()
    HttpService:PostAsync(url, HttpService:JSONEncode(event), Enum.HttpContentType.ApplicationJson)
  end)
end

return BackendClient
```

### 6.4 `ServerScriptService/MissionRouter.server.lua`

```lua
-- Script (server)
local Players = game:GetService("Players")
local HttpService = game:GetService("HttpService")
local TeleportService = game:GetService("TeleportService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Remotes = require(ReplicatedStorage.Remotes)
local BackendClient = require(script.Parent.BackendClient)

local sessionsByPlayer = {}   -- userId -> { plan, session_id, missionIndex }

local function loadPlanForPlayer(player)
  -- Read plan_id from TeleportService join data or fallback
  local joinData = player:GetJoinData()
  local planId
  if joinData and joinData.LaunchData and joinData.LaunchData ~= "" then
    local ok, decoded = pcall(HttpService.JSONDecode, HttpService, joinData.LaunchData)
    if ok and decoded and decoded.plan_id then planId = decoded.plan_id end
  end

  -- DEMO FALLBACK: if no launchData, use hardcoded test plan_id
  if not planId then
    planId = "HARDCODED_DEMO_PLAN_ID"  -- replace with a plan_id you pre-generate
  end

  local config = BackendClient:getConfig(planId)
  if not config then
    warn("Could not load config, kicking player")
    player:Kick("Failed to load your mission. Please try again.")
    return
  end

  sessionsByPlayer[player.UserId] = {
    plan = config.plan,
    session_id = config.session_id,
    missionIndex = 1,
  }

  Remotes.LoadPlan:FireClient(player, config.plan)
  wait(1)
  Remotes.StartMission:FireClient(player, config.plan.missions[1])
end

Players.PlayerAdded:Connect(loadPlanForPlayer)

-- Client reports mission complete
Remotes.MissionResult.OnServerEvent:Connect(function(player, missionId, success)
  local sess = sessionsByPlayer[player.UserId]
  if not sess then return end

  BackendClient:report({
    session_id = sess.session_id,
    mission_id = missionId,
    event_type = success and "mission_completed" or "mission_failed",
    payload = {},
  })

  if success then
    sess.missionIndex = sess.missionIndex + 1
    local next = sess.plan.missions[sess.missionIndex]
    if next then
      Remotes.StartMission:FireClient(player, next)
    else
      -- Done!
      Remotes.LoadPlan:FireClient(player, { done = true, plan = sess.plan })
    end
  end
end)

-- NPC chat proxy
Remotes.NpcChat.OnServerInvoke = function(player, mission, playerMessage, history)
  local sess = sessionsByPlayer[player.UserId]
  if not sess then return { npc_reply = "...", is_correct_answer = false } end
  return BackendClient:npcChat({
    session_id = sess.session_id,
    mission_id = mission.mission_id,
    npc_name = mission.npc_name,
    npc_persona = mission.npc_persona,
    topic = sess.plan.topic,
    player_message = playerMessage,
    conversation_history = history or {},
  })
end

-- Puzzle submission
Remotes.SubmitPuzzle.OnServerInvoke = function(player, missionId, submittedOrder)
  local sess = sessionsByPlayer[player.UserId]
  if not sess then return false end
  local mission
  for _, m in ipairs(sess.plan.missions) do
    if m.mission_id == missionId then mission = m; break end
  end
  if not mission or mission.type ~= "puzzle" then return false end

  if #submittedOrder ~= #mission.correct_order then return false end
  for i, v in ipairs(submittedOrder) do
    if v ~= mission.correct_order[i] then return false end
  end
  return true
end

-- Exploration target collection
Remotes.CollectTarget.OnServerEvent:Connect(function(player, missionId, targetTag)
  local sess = sessionsByPlayer[player.UserId]
  if not sess then return end
  -- Client-side tracks the collected set; server just reports.
  BackendClient:report({
    session_id = sess.session_id,
    mission_id = missionId,
    event_type = "answer_submitted",
    payload = { target = targetTag },
  })
end)
```

### 6.5 `StarterPlayerScripts/ClientBootstrap.client.lua`

```lua
-- LocalScript
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Remotes = require(ReplicatedStorage.Remotes)
local DialogueMission = require(ReplicatedStorage.MissionModules.DialogueMission)
local PuzzleMission = require(ReplicatedStorage.MissionModules.PuzzleMission)
local ExplorationMission = require(ReplicatedStorage.MissionModules.ExplorationMission)
local HUD = require(ReplicatedStorage.UI.HUD)

local player = Players.LocalPlayer
local currentMission = nil

local function teleportToLocation(location)
  local spawnName = "Spawn_" .. location
  local spawn = Workspace:FindFirstChild(spawnName, true)
  if spawn and player.Character then
    player.Character:PivotTo(spawn.CFrame + Vector3.new(0, 3, 0))
  end
end

HUD.mount()

Remotes.LoadPlan.OnClientEvent:Connect(function(payload)
  if payload.done then
    HUD.setStatus("Adventure complete! You mastered: " .. payload.plan.title)
    return
  end
  HUD.setPlanTitle(payload.title)
end)

Remotes.StartMission.OnClientEvent:Connect(function(mission)
  currentMission = mission
  teleportToLocation(mission.location)
  HUD.setMission(mission)

  if mission.type == "dialogue" then
    DialogueMission.start(mission, function(success)
      Remotes.MissionResult:FireServer(mission.mission_id, success)
    end)
  elseif mission.type == "puzzle" then
    PuzzleMission.start(mission, function(success)
      Remotes.MissionResult:FireServer(mission.mission_id, success)
    end)
  elseif mission.type == "exploration" then
    ExplorationMission.start(mission, function(success)
      Remotes.MissionResult:FireServer(mission.mission_id, success)
    end)
  end
end)
```

### 6.6 `ReplicatedStorage/MissionModules/DialogueMission.lua`

```lua
-- ModuleScript
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Remotes = require(ReplicatedStorage.Remotes)
local DialogueUI = require(ReplicatedStorage.UI.DialogueUI)

local M = {}

function M.start(mission, onComplete)
  local history = {}
  DialogueUI.open({
    npcName = mission.npc_name,
    openingLine = mission.opening_line,
    onPlayerMessage = function(text)
      table.insert(history, {role = "player", content = text})
      local resp = Remotes.NpcChat:InvokeServer(mission, text, history)
      if resp then
        table.insert(history, {role = "npc", content = resp.npc_reply})
        DialogueUI.showNpcLine(resp.npc_reply)
        if resp.is_correct_answer then
          wait(2)
          DialogueUI.close()
          onComplete(true)
        end
      end
    end,
    onClose = function() onComplete(false) end,
  })
end

return M
```

### 6.7 `ReplicatedStorage/MissionModules/PuzzleMission.lua`

```lua
-- ModuleScript
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Remotes = require(ReplicatedStorage.Remotes)
local PuzzleUI = require(ReplicatedStorage.UI.PuzzleUI)

local M = {}

function M.start(mission, onComplete)
  PuzzleUI.open({
    prompt = mission.prompt,
    items = mission.items,
    onSubmit = function(order)
      local ok = Remotes.SubmitPuzzle:InvokeServer(mission.mission_id, order)
      if ok then
        PuzzleUI.showSuccess()
        wait(1.5)
        PuzzleUI.close()
        onComplete(true)
      else
        PuzzleUI.showFailure("Try again — think about the order.")
      end
    end,
  })
end

return M
```

### 6.8 `ReplicatedStorage/MissionModules/ExplorationMission.lua`

```lua
-- ModuleScript
local Workspace = game:GetService("Workspace")
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local Remotes = require(ReplicatedStorage.Remotes)
local HUD = require(ReplicatedStorage.UI.HUD)

local M = {}

function M.start(mission, onComplete)
  local remaining = {}
  for _, t in ipairs(mission.targets) do remaining[t] = true end

  HUD.setMissionInstruction(mission.prompt .. (mission.hint and (" — Hint: " .. mission.hint) or ""))
  HUD.setTargets(mission.targets, {})

  local collected = {}
  local conn

  local function onClickPart(part)
    for _, tag in ipairs(CollectionService:GetTags(part)) do
      if remaining[tag] then
        remaining[tag] = nil
        table.insert(collected, tag)
        Remotes.CollectTarget:FireServer(mission.mission_id, tag)
        HUD.setTargets(mission.targets, collected)
        if next(remaining) == nil then
          if conn then conn:Disconnect() end
          onComplete(true)
        end
        return
      end
    end
  end

  conn = UserInputService.InputBegan:Connect(function(input, gp)
    if gp then return end
    if input.UserInputType == Enum.UserInputType.MouseButton1 then
      local mouse = Players.LocalPlayer:GetMouse()
      if mouse.Target then onClickPart(mouse.Target) end
    end
  end)
end

return M
```

### 6.9 `ReplicatedStorage/UI/DialogueUI.lua` (skeleton)

```lua
-- ModuleScript
local Players = game:GetService("Players")

local DialogueUI = {}
local gui, npcLabel, input, sendBtn, closeBtn
local currentHandlers

local function buildGui()
  local player = Players.LocalPlayer
  gui = Instance.new("ScreenGui")
  gui.Name = "DialogueUI"
  gui.ResetOnSpawn = false
  gui.Parent = player:WaitForChild("PlayerGui")

  local frame = Instance.new("Frame", gui)
  frame.Size = UDim2.new(0, 600, 0, 250)
  frame.Position = UDim2.new(0.5, -300, 1, -280)
  frame.BackgroundColor3 = Color3.fromRGB(30, 25, 20)
  frame.BorderSizePixel = 0

  local title = Instance.new("TextLabel", frame)
  title.Name = "NpcName"
  title.Size = UDim2.new(1, -20, 0, 30)
  title.Position = UDim2.new(0, 10, 0, 5)
  title.BackgroundTransparency = 1
  title.TextColor3 = Color3.fromRGB(255, 220, 130)
  title.Font = Enum.Font.GothamBold
  title.TextSize = 20
  title.TextXAlignment = Enum.TextXAlignment.Left

  npcLabel = Instance.new("TextLabel", frame)
  npcLabel.Size = UDim2.new(1, -20, 0, 100)
  npcLabel.Position = UDim2.new(0, 10, 0, 40)
  npcLabel.BackgroundTransparency = 1
  npcLabel.TextColor3 = Color3.new(1, 1, 1)
  npcLabel.Font = Enum.Font.Gotham
  npcLabel.TextSize = 16
  npcLabel.TextWrapped = true
  npcLabel.TextXAlignment = Enum.TextXAlignment.Left
  npcLabel.TextYAlignment = Enum.TextYAlignment.Top

  input = Instance.new("TextBox", frame)
  input.Size = UDim2.new(1, -140, 0, 40)
  input.Position = UDim2.new(0, 10, 1, -50)
  input.PlaceholderText = "Speak..."
  input.Text = ""
  input.ClearTextOnFocus = false
  input.Font = Enum.Font.Gotham
  input.TextSize = 16

  sendBtn = Instance.new("TextButton", frame)
  sendBtn.Size = UDim2.new(0, 60, 0, 40)
  sendBtn.Position = UDim2.new(1, -130, 1, -50)
  sendBtn.Text = "Send"
  sendBtn.BackgroundColor3 = Color3.fromRGB(180, 120, 40)
  sendBtn.TextColor3 = Color3.new(1,1,1)

  closeBtn = Instance.new("TextButton", frame)
  closeBtn.Size = UDim2.new(0, 60, 0, 40)
  closeBtn.Position = UDim2.new(1, -65, 1, -50)
  closeBtn.Text = "Leave"
  closeBtn.BackgroundColor3 = Color3.fromRGB(70, 30, 30)
  closeBtn.TextColor3 = Color3.new(1,1,1)

  sendBtn.MouseButton1Click:Connect(function()
    if input.Text ~= "" and currentHandlers then
      local msg = input.Text
      input.Text = ""
      currentHandlers.onPlayerMessage(msg)
    end
  end)
  closeBtn.MouseButton1Click:Connect(function()
    if currentHandlers then currentHandlers.onClose() end
    DialogueUI.close()
  end)
end

function DialogueUI.open(handlers)
  if not gui then buildGui() end
  currentHandlers = handlers
  gui.Enabled = true
  gui:FindFirstChild("Frame").NpcName.Text = handlers.npcName
  npcLabel.Text = handlers.openingLine
end

function DialogueUI.showNpcLine(text)
  npcLabel.Text = text
end

function DialogueUI.close()
  if gui then gui.Enabled = false end
  currentHandlers = nil
end

return DialogueUI
```

### 6.10 `ReplicatedStorage/UI/PuzzleUI.lua` (skeleton)

Build a Frame with buttons for each item; clicking an item appends it to `order`; a "Submit" button calls `handlers.onSubmit(order)`. Follow the same pattern as `DialogueUI`. Left as a straightforward implementation for the AI to fill in — the contract is:

```
PuzzleUI.open({ prompt = string, items = {string}, onSubmit = function(order: {number}) })
PuzzleUI.showSuccess()
PuzzleUI.showFailure(msg)
PuzzleUI.close()
```

### 6.11 `ReplicatedStorage/UI/HUD.lua` (skeleton)

Top-of-screen status showing plan title, current mission summary, and (for exploration) a checklist of `targets` with checkmarks.

```
HUD.mount()
HUD.setPlanTitle(title)
HUD.setMission(mission)
HUD.setMissionInstruction(text)
HUD.setTargets(targets, collectedArray)
HUD.setStatus(text)
```

### 6.12 NPC spawn logic

In `MissionRouter.server.lua`, when starting a dialogue mission, spawn a Model into the correct location. For hackathon, use `Workspace.NPCs.[npc_name]` if it exists, otherwise clone a default `NPCTemplate` from `ServerStorage`. Name it after the persona for visual variety.

---

## 7. End-to-end demo flow

1. `uvicorn` running locally, tunneled via **ngrok** (`ngrok http 8000`) so Roblox can reach it.
2. Copy the ngrok URL into `BackendClient.lua` as `BASE` and into `web/.env.local` as `NEXT_PUBLIC_BACKEND_URL`.
3. Web app on `localhost:3000`. Upload an Ancient Egypt PDF.
4. Backend extracts text → LLM generates plan → returned to web.
5. Preview screen shows plan. User clicks **Launch in Roblox**.
6. Roblox opens the published place with `launchData={"plan_id":"..."}`.
7. Server-side `MissionRouter` reads `launchData`, calls `/api/config`, gets plan.
8. First mission (`dialogue`) fires → client teleports to `pyramid_entrance`, dialogue UI opens.
9. Player chats with NPC. Each turn: client → server → `/api/npc-chat` → response.
10. When `is_correct_answer` is true, mission ends, next mission starts.
11. Puzzle mission → drag/click items into order → submit → server validates.
12. Exploration → click tagged Parts → all collected → done.
13. HUD shows completion. Web can hit `/api/report/{session_id}` to show summary.

---

## 8. Manual test script (rehearse before demo)

1. Backend `/health` returns `{ ok: true }`.
2. Upload a known 3-page PDF → returns `upload_id` and 500-char preview.
3. Generate → returns a valid plan with 3 objectives + 3 missions of distinct types.
4. Open preview page → all fields render.
5. Click Launch → Roblox opens the place.
6. In Studio, run once and confirm HTTP call returns a plan.
7. First NPC dialogue: send a wrong answer → NPC replies in character, no [CORRECT]. Send a correct answer → mission ends.
8. Puzzle: try wrong order first → failure. Correct order → success.
9. Exploration: click tagged Parts → HUD updates → completion fires.
10. Report endpoint shows `missions_completed: 3`.

---

## 9. Deployment (when local demo works)

- **Backend:** `railway up` or Render. Set env vars. Note the public URL.
- **Web:** `vercel deploy`. Set `NEXT_PUBLIC_BACKEND_URL` and `NEXT_PUBLIC_ROBLOX_PLACE_ID`.
- **Roblox:** update `BASE` in `BackendClient.lua`, republish place.

---

## 10. Non-negotiables (things that MUST work)

1. Backend generates a **valid, schema-conformant Mission Plan JSON** every time. Retry on JSON parse failure once, then error clearly.
2. Roblox place **loads a plan from launchData** and picks a sensible fallback if launchData is missing.
3. Dialogue NPC produces **a correct-answer signal** the server can act on. The `[CORRECT]`/`correct:true` signal from the LLM is the source of truth.
4. Puzzle validation is **server-side**. Client never decides success.
5. HttpService calls are **wrapped in pcall**. Any failure logs and does not crash the player experience.

---

## 11. Things NOT to build for the hackathon

- User accounts, auth, sessions
- Databases (in-memory dicts are fine)
- Persistent progress across joins
- Multi-player
- Editing the mission plan
- Any topic other than Ancient Egypt
- Any mission types other than the three specified
- Voice, avatars, cosmetics
- Analytics beyond the `/api/report` endpoint
