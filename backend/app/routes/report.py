from fastapi import APIRouter
from app.models.schemas import ReportEvent
from app.services import storage, everos_memory

router = APIRouter()

@router.post("/report")
def report(event: ReportEvent):
    storage.append_event(event)
    if event.event_type in {"mission_completed", "mission_failed"}:
        learner_id = storage.get_session_learner(event.session_id)
        everos_memory.remember_turns(
            learner_id,
            event.session_id,
            [{
                "role": "assistant",
                "content": (
                    f"Learning event: {event.event_type} for mission "
                    f"{event.mission_id}. Evidence: {str(event.payload)[:500]}"
                ),
            }],
        )
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
