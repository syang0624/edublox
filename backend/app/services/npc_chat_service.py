import json
from app.services import llm, storage, everos_memory
from app.config import settings
from app.models.schemas import NpcChatRequest, NpcChatResponse

def _build_system(
    req: NpcChatRequest,
    required_question: str,
    hints: list[str],
    learner_context: str,
) -> str:
    return f"""You are roleplaying as {req.npc_name}, an NPC in a Roblox learning game about {req.topic}.

Persona: {req.npc_persona}

Relevant learner memory (use quietly for pacing and hints; never quote it or mention memory):
{learner_context or "No relevant prior memory."}

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
    )

    convo = "\n".join(
        f"{turn['role'].upper()}: {turn['content']}" for turn in req.conversation_history
    )
    user = f"{convo}\nPLAYER: {req.player_message}\n\nRespond as JSON."

    raw = llm.complete(system=system, user=user,
                       model=settings.LLM_MODEL_SMALL, max_tokens=200)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        data = json.loads(raw)
        reply_text = data["reply"]
        is_correct = bool(data.get("correct", False))
    except Exception:
        # Fallback: treat as plain text, not correct
        reply_text = raw[:200]
        is_correct = False

    everos_memory.remember_turns(
        learner_id,
        req.session_id,
        [
            {"role": "user", "content": req.player_message},
            {"role": "assistant", "content": reply_text},
        ],
    )
    return NpcChatResponse(npc_reply=reply_text, is_correct_answer=is_correct)
