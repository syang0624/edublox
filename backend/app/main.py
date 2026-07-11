import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.models.schemas import MissionPlan
from app.routes import upload, generate, config, npc_chat, report, memory
from app.services import storage, everos_memory

log = logging.getLogger(__name__)

DEMO_DIR = Path(__file__).parent / "demo"

# Demo plan file -> the EverOS learner it belongs to. kai_tanaka is the
# presentation persona (seeded via assets/create.json) whose history shows
# gravity already mastered — Newton's laws is his next step.
DEMO_PLANS = {
    "solar_system_plan.json": "demo_learner",
    "newton_laws_plan.json": "kai_tanaka",
}

def _seed_demo_plans() -> None:
    # Seeding failure must never prevent startup (PRD 4.15).
    for filename, learner_id in DEMO_PLANS.items():
        try:
            data = json.loads((DEMO_DIR / filename).read_text())
            plan = MissionPlan(**data)
            storage.save_plan(plan, learner_id)
            log.info("Seeded demo plan %s (learner %s)", plan.plan_id, learner_id)
        except Exception as exc:
            log.warning("Could not seed demo plan %s: %s", filename, exc)

@asynccontextmanager
async def lifespan(app: FastAPI):
    _seed_demo_plans()
    yield
    # Await queued EverOS writes so the last interaction is not lost.
    everos_memory.shutdown()

app = FastAPI(title="Learning Universe API", lifespan=lifespan)

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
app.include_router(memory.router, prefix="/api")

@app.get("/health")
def health():
    return {"ok": True}
