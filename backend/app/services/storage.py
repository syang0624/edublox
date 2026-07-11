# Operational state with a write-through cache: memory is the fast path,
# Butterbase's data API is the durable copy, so a backend restart no longer
# invalidates live plan URLs, sessions, or reports. Reads fall back to
# Butterbase on a cache miss; if Butterbase is unreachable everything
# degrades to in-memory-only, mirroring the EverOS resilience pattern.
# Durable learner context still belongs in EverOS — Butterbase holds app
# state, not what the product has learned about a learner.
from typing import Dict
from app.models.schemas import MissionPlan, ReportEvent
from app.services import butterbase_db

_uploads: Dict[str, str] = {}        # upload_id -> extracted_text
_plans: Dict[str, MissionPlan] = {}  # plan_id -> MissionPlan
_sessions: Dict[str, str] = {}       # session_id -> plan_id
_plan_learners: Dict[str, str] = {}  # plan_id -> EverOS user_id
_events: list = []                   # list of ReportEvent


def save_upload(upload_id: str, text: str):
    _uploads[upload_id] = text
    butterbase_db.upsert(
        "uploads", upload_id, {"upload_id": upload_id, "text": text}
    )


def get_upload(upload_id: str) -> str:
    if upload_id not in _uploads:
        row = butterbase_db.fetch("uploads", upload_id)
        if row is None:
            raise KeyError(upload_id)
        _uploads[upload_id] = row["text"]
    return _uploads[upload_id]


def save_plan(plan: MissionPlan, learner_id: str):
    _plans[plan.plan_id] = plan
    _plan_learners[plan.plan_id] = learner_id
    butterbase_db.upsert("plans", plan.plan_id, {
        "plan_id": plan.plan_id,
        "plan_json": plan.model_dump(),
        "learner_id": learner_id,
    })


def get_plan(plan_id: str) -> MissionPlan:
    if plan_id not in _plans:
        row = butterbase_db.fetch("plans", plan_id)
        if row is None:
            raise KeyError(plan_id)
        # Re-validate through the canonical schema so the data contract
        # stays in one place.
        _plans[plan_id] = MissionPlan.model_validate(row["plan_json"])
        _plan_learners[plan_id] = row["learner_id"]
    return _plans[plan_id]


def create_session(plan_id: str) -> str:
    import uuid
    sid = uuid.uuid4().hex
    _sessions[sid] = plan_id
    butterbase_db.upsert(
        "sessions", sid, {"session_id": sid, "plan_id": plan_id}
    )
    return sid


def _session_plan_id(session_id: str) -> str:
    if session_id not in _sessions:
        row = butterbase_db.fetch("sessions", session_id)
        if row is None:
            raise KeyError(session_id)
        _sessions[session_id] = row["plan_id"]
    return _sessions[session_id]


def get_session_plan(session_id: str) -> MissionPlan:
    return get_plan(_session_plan_id(session_id))


def get_session_learner(session_id: str) -> str:
    plan_id = _session_plan_id(session_id)
    get_plan(plan_id)  # rehydrates _plan_learners on a cache miss
    return _plan_learners[plan_id]


def append_event(event: ReportEvent):
    _events.append(event)
    butterbase_db.insert("events", {
        "session_id": event.session_id,
        "mission_id": event.mission_id,
        "event_type": event.event_type,
        "payload": event.payload,
    })


def events_for_session(session_id: str):
    local = [e for e in _events if e.session_id == session_id]
    rows = butterbase_db.fetch_all(
        "events", {"session_id": f"eq.{session_id}"}
    )
    if rows is None:
        return local
    remote = [
        ReportEvent(
            session_id=r["session_id"],
            mission_id=r["mission_id"],
            event_type=r["event_type"],
            payload=r.get("payload") or {},
        )
        for r in rows
    ]
    # Writes are best-effort: prefer whichever side saw more of the
    # session (remote misses events written during an outage; local
    # misses events from before a restart).
    return remote if len(remote) >= len(local) else local
