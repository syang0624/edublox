from fastapi import APIRouter, HTTPException
from app.models.schemas import ReportEvent
from app.services import storage, everos_memory

router = APIRouter()

# Events worth remembering. mission_started is operational noise; the rest
# carry learning or engagement signal.
_MEMORY_EVENTS = {
    "mission_completed", "mission_failed", "answer_submitted",
    "behavior_signal",
}


def _mission_summary(mission, mission_id: str) -> str:
    # mission_id alone ("m2") means nothing across sessions because every
    # plan regenerates — describe the actual concept so EverOS extraction
    # has something to distill.
    if mission is None:
        return f"mission {mission_id}"
    if mission.type == "dialogue":
        return f'the question "{mission.required_question}"'
    if mission.type == "puzzle":
        items = ", ".join(mission.items)
        return f'the ordering puzzle "{mission.prompt}" (items: {items})'
    if mission.type == "simulation":
        boxes = ", ".join(
            f"{b.label} {b.mass_kg:g} kg" for b in mission.boxes
        )
        return (
            f'the F=ma crate-push simulation (crates: {boxes}; '
            f'quiz: "{mission.quiz.question}")'
        )
    return f'the exploration task "{mission.prompt}"'


def _memory_line(event: ReportEvent, plan, mission) -> str:
    what = _mission_summary(mission, event.mission_id)
    detail = str(event.payload)[:400] if event.payload else ""
    if event.event_type == "behavior_signal":
        return (
            f"Engagement observation while the learner worked on {what} "
            f"(topic: {plan.topic}): {detail}"
        )
    if event.event_type == "answer_submitted":
        return (
            f"The learner submitted an answer to {what} "
            f"(topic: {plan.topic}): {detail}"
        )
    verb = "completed" if event.event_type == "mission_completed" else "failed"
    line = f"The learner {verb} {what} (topic: {plan.topic})."
    return f"{line} Evidence: {detail}" if detail else line


@router.post("/report")
def report(event: ReportEvent):
    storage.append_event(event)
    if event.event_type not in _MEMORY_EVENTS:
        return {"ok": True}
    try:
        plan = storage.get_session_plan(event.session_id)
        learner_id = storage.get_session_learner(event.session_id)
    except KeyError:
        raise HTTPException(404, "session_id not found")
    mission = next(
        (m for m in plan.missions if m.mission_id == event.mission_id), None
    )
    # Dialogue answers already reach memory as full NPC chat transcripts.
    if (
        event.event_type == "answer_submitted"
        and mission is not None
        and mission.type == "dialogue"
    ):
        return {"ok": True}
    everos_memory.remember_turns(
        learner_id,
        event.session_id,
        [{"role": "assistant", "content": _memory_line(event, plan, mission)}],
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
