# Ephemeral operational state only: uploaded text, generated plans, live launch
# mappings, and the report view. Durable learner context belongs in EverOS —
# a backend restart may invalidate an active plan URL, but it must not erase
# what the product has learned about a learner.
from typing import Dict
from app.models.schemas import MissionPlan

_uploads: Dict[str, str] = {}       # upload_id -> extracted_text
_plans: Dict[str, MissionPlan] = {} # plan_id -> MissionPlan
_sessions: Dict[str, str] = {}      # session_id -> plan_id
_plan_learners: Dict[str, str] = {} # plan_id -> EverOS user_id
_events: list = []                  # list of ReportEvent

def save_upload(upload_id: str, text: str): _uploads[upload_id] = text
def get_upload(upload_id: str) -> str: return _uploads[upload_id]

def save_plan(plan: MissionPlan, learner_id: str):
    _plans[plan.plan_id] = plan
    _plan_learners[plan.plan_id] = learner_id

def get_plan(plan_id: str) -> MissionPlan: return _plans[plan_id]

def create_session(plan_id: str) -> str:
    import uuid
    sid = uuid.uuid4().hex
    _sessions[sid] = plan_id
    return sid

def get_session_plan(session_id: str) -> MissionPlan:
    plan_id = _sessions[session_id]
    return _plans[plan_id]

def get_session_learner(session_id: str) -> str:
    plan_id = _sessions[session_id]
    return _plan_learners[plan_id]

def append_event(event): _events.append(event)
def events_for_session(session_id: str):
    return [e for e in _events if e.session_id == session_id]
