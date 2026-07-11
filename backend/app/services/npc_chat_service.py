import json
import re
from app.services import llm, storage, everos_memory
from app.config import settings
from app.models.schemas import NpcChatRequest, NpcChatResponse

def _session_events_block(session_id: str, current_mission_id: str) -> str:
    # Live session awareness: what the player has done (and how they are
    # behaving) since joining, so the NPC can adapt mid-session — e.g.
    # acknowledge a just-failed puzzle or notice signs of boredom.
    try:
        events = storage.events_for_session(session_id)[-6:]
    except Exception:
        return ""
    lines = []
    for e in events:
        detail = str(e.payload)[:100] if e.payload else ""
        marker = " (this mission)" if e.mission_id == current_mission_id else ""
        lines.append(f"- {e.event_type}{marker}: {detail}".rstrip(": "))
    return "\n".join(lines)


def _build_system(
    req: NpcChatRequest,
    required_question: str,
    hints: list[str],
    learner_context: str,
    session_events: str,
) -> str:
    return f"""You are roleplaying as {req.npc_name}, an NPC in a Roblox learning game about {req.topic}.

Persona: {req.npc_persona}

Relevant learner memory (use quietly for pacing and hints; never quote it or mention memory):
{learner_context or "No relevant prior memory."}

What has happened so far in this play session (react naturally when relevant — e.g. acknowledge something they just failed, or re-engage a player who seems distracted or bored; never mention logs or tracking):
{session_events or "Nothing notable yet."}

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
    learner_id = storage.get_session_learner(req.session_id)
    mission = next(m for m in plan.missions if m.mission_id == req.mission_id)
    learner_context = everos_memory.recall(
        learner_id,
        f"Helpful context for answering {mission.required_question}",
    )
    system = _build_system(
        req,
        mission.required_question,
        mission.correct_answer_hints,
        learner_context,
        _session_events_block(req.session_id, req.mission_id),
    )

    convo = "\n".join(
        f"{turn['role'].upper()}: {turn['content']}" for turn in req.conversation_history
    )
    user = f"{convo}\nPLAYER: {req.player_message}\n\nRespond as JSON."

    raw = llm.complete(system=system, user=user,
                       model=settings.LLM_MODEL_SMALL, max_tokens=400)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        data = json.loads(raw)
        reply_text = data["reply"]
        is_correct = bool(data.get("correct", False))
    except Exception:
        # Salvage a truncated/malformed JSON response so raw JSON never
        # reaches the player.
        reply_match = re.search(r'"reply"\s*:\s*"((?:[^"\\]|\\.)*)', raw)
        correct_match = re.search(r'"correct"\s*:\s*(true|tru|tr|t\b)', raw)
        if reply_match:
            try:
                reply_text = json.loads(f'"{reply_match.group(1)}"')[:200]
            except Exception:
                reply_text = reply_match.group(1)[:200]
            is_correct = correct_match is not None
        else:
            reply_text = raw[:200]
            is_correct = False

    # The prompt's [CORRECT] token is a signal, not player-facing copy.
    if "[CORRECT]" in reply_text:
        is_correct = True
        reply_text = reply_text.replace("[CORRECT]", "").strip()

    everos_memory.remember_turns(
        learner_id,
        req.session_id,
        [
            {"role": "user", "content": req.player_message},
            {"role": "assistant", "content": reply_text},
        ],
    )
    return NpcChatResponse(npc_reply=reply_text, is_correct_answer=is_correct)
