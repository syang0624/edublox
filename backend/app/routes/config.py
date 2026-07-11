# Roblox hits this on player join. Plan is returned by plan_id (query param) —
# no auth for hackathon.
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
    return ConfigResponse(
        plan=plan,
        session_id=session_id,
        learner_id=storage.get_session_learner(session_id),
    )
