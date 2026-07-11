# EverOS is the only durable learner-memory layer. It stores the session data
# from each Roblox game session (NPC chat turns + mission milestone events) as
# raw transcripts; EverOS's extraction pipeline distills them into the
# learner's `profile` (persistent traits) and `episodic_memory` (what
# happened), which is why recall searches both memory types.
# Failure must degrade gracefully: log it, continue without recalled context,
# and never block the Roblox session.
import logging
import time
from concurrent.futures import ThreadPoolExecutor
import httpx
from app.config import settings

log = logging.getLogger(__name__)
_writes = ThreadPoolExecutor(max_workers=2, thread_name_prefix="everos-write")


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.EVEROS_API_KEY}"}


def format_memory_results(payload: dict) -> str:
    ignored_keys = {
        "id", "task_id", "user_id", "session_id",
        "created_at", "updated_at", "status",
        # EverOS episode/profile metadata and fields that duplicate the
        # full "episode" text — they waste the 1,500-char context budget.
        "group_id", "timestamp", "participants", "type",
        "parent_type", "parent_id", "parent_episode_id",
        "original_text", "summary", "subject",
        "item_id", "item_type", "scenario",
    }
    snippets: list[str] = []

    def walk(value, key: str = "") -> None:
        if (
            isinstance(value, str)
            and key not in ignored_keys
            and len(value.strip()) > 2
        ):
            snippets.append(value.strip())
        elif isinstance(value, list):
            for item in value:
                walk(item, key)
        elif isinstance(value, dict):
            for child_key, child_value in value.items():
                walk(child_value, child_key)

    data = payload.get("data", payload)
    if isinstance(data, dict):
        # Drop the request echo ({"query": {"text": ..., "method": ...}})
        # so it never pollutes the recalled context.
        data = {k: v for k, v in data.items() if k != "query"}
    walk(data)
    deduped = list(dict.fromkeys(snippets))
    return "\n".join(deduped)[:1500]


def recall(learner_id: str, query: str) -> str:
    if not settings.EVEROS_API_KEY:
        return ""
    try:
        response = httpx.post(
            f"{settings.EVEROS_BASE_URL}/memories/search",
            headers=_headers(),
            json={
                "query": query,
                "method": "hybrid",
                "memory_types": ["episodic_memory", "profile"],
                "top_k": 5,
                "filters": {"user_id": learner_id},
            },
            timeout=8,
        )
        response.raise_for_status()
        return format_memory_results(response.json())  # max 1,500 chars
    except Exception as exc:
        log.warning("EverOS recall unavailable: %s", exc)
        return ""


def remember_turns(
    learner_id: str, session_id: str, messages: list[dict]
) -> None:
    # Do not add EverOS write latency to gameplay responses.
    _writes.submit(_write_turns, learner_id, session_id, messages)


def shutdown() -> None:
    # Await queued writes on graceful shutdown so the last interaction is
    # not lost.
    _writes.shutdown(wait=True)


def _write_turns(
    learner_id: str, session_id: str, messages: list[dict]
) -> None:
    if not settings.EVEROS_API_KEY:
        return
    now_ms = int(time.time() * 1000)
    payload_messages = [
        {**message, "timestamp": message.get("timestamp", now_ms + index)}
        for index, message in enumerate(messages)
    ]
    try:
        response = httpx.post(
            f"{settings.EVEROS_BASE_URL}/memories",
            headers=_headers(),
            json={
                "user_id": learner_id,
                "session_id": session_id,
                "messages": payload_messages,
                "async_mode": False,
            },
            timeout=12,
        )
        response.raise_for_status()
        # Extraction is triggered by semantic boundary detection; a trailing
        # chunk with no follow-up never hits a boundary on its own. Flush so
        # the turns are distilled into profile/episodic memory and become
        # searchable for the next recall.
        flush = httpx.post(
            f"{settings.EVEROS_BASE_URL}/memories/flush",
            headers=_headers(),
            json={"user_id": learner_id, "session_id": session_id},
            timeout=30,
        )
        flush.raise_for_status()
    except Exception as exc:
        log.warning("EverOS write unavailable: %s", exc)
