# Memory reveal: exposes what EverOS actually remembers about a learner —
# the same labeled recalls the plan generator is shown. Powers the
# "what the tutor remembers" panel in the web app and the demo's
# open-the-memory moment.
from fastapi import APIRouter
from app.services import everos_memory

router = APIRouter()


@router.get("/memory/{learner_id}")
def get_memory(learner_id: str):
    return {
        "learner_id": learner_id,
        "memory": everos_memory.recall_many(
            learner_id, everos_memory.LEARNER_RECALL_QUERIES
        ),
    }
