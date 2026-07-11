import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.models.schemas import MissionPlan
from app.routes import upload, generate, config, npc_chat, report
from app.services import storage, everos_memory

log = logging.getLogger(__name__)

DEMO_PLAN_PATH = Path(__file__).parent / "demo" / "solar_system_plan.json"

def _seed_demo_plan() -> None:
    # Seeding failure must never prevent startup (PRD 4.15).
    try:
        data = json.loads(DEMO_PLAN_PATH.read_text())
        plan = MissionPlan(**data)
        storage.save_plan(plan, "demo_learner")
        log.info("Seeded demo plan %s", plan.plan_id)
    except Exception as exc:
        log.warning("Could not seed demo solar system plan: %s", exc)

@asynccontextmanager
async def lifespan(app: FastAPI):
    _seed_demo_plan()
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

@app.get("/health")
def health():
    return {"ok": True}
