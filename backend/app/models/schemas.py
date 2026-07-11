from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from enum import Enum

class MissionType(str, Enum):
    DIALOGUE = "dialogue"
    PUZZLE = "puzzle"
    EXPLORATION = "exploration"
    SIMULATION = "simulation"

class DialogueMission(BaseModel):
    type: Literal["dialogue"] = "dialogue"
    mission_id: str
    location: Literal["orbital_station", "alien_planet", "asteroid_field"]
    npc_name: str                       # e.g., "Commander Nova"
    npc_persona: str                    # 1-2 sentences, in-character behavior brief
    opening_line: str                   # what NPC says when player approaches
    required_question: str              # the question player must correctly answer
    correct_answer_hints: List[str]     # 3-5 keywords/phrases judged as correct
    success_line: str                   # NPC line on correct answer
    max_attempts: int = 3

class PuzzleMission(BaseModel):
    type: Literal["puzzle"] = "puzzle"
    mission_id: str
    location: Literal["orbital_station", "alien_planet", "asteroid_field"]
    prompt: str                         # "Restore the research log sequence"
    items: List[str]                    # display strings, presented shuffled
    correct_order: List[int]            # indices into items in the correct order

class ExplorationMission(BaseModel):
    type: Literal["exploration"] = "exploration"
    mission_id: str
    location: Literal["orbital_station", "alien_planet", "asteroid_field"]
    prompt: str                         # "Scan 3 objects that match the lesson"
    targets: List[str]                  # object tags in the scene
    hint: Optional[str] = None

class SimBox(BaseModel):
    label: str                          # display name, e.g. "Light Crate"
    mass_kg: float                      # drives the physics + speed gauge

class SimQuiz(BaseModel):
    question: str
    choices: List[str]                  # multiple choice, shown as buttons
    correct_index: int                  # index into choices
    explanation: str                    # shown after the player answers

class SimulationMission(BaseModel):
    # Hands-on physics sim: player pushes crates of different masses with
    # the same force, watches the speed gauge, then answers a quiz.
    type: Literal["simulation"] = "simulation"
    mission_id: str
    location: Literal["orbital_station", "alien_planet", "asteroid_field"]
    prompt: str                         # on-screen instruction for the sim
    boxes: List[SimBox]                 # crates to push
    quiz: SimQuiz                       # end-of-mission check

Mission = DialogueMission | PuzzleMission | ExplorationMission | SimulationMission

class MissionPlan(BaseModel):
    plan_id: str
    title: str                          # "Voyage Through Living Systems"
    topic: str                          # concise subject inferred from the source PDF
    objectives: List[str]               # 3 short learning objectives
    missions: List[Mission]             # exactly 3 missions, one of each type is ideal

class UploadResponse(BaseModel):
    upload_id: str
    extracted_text_preview: str         # first 500 chars for user confirmation
    char_count: int

class GenerateRequest(BaseModel):
    upload_id: str
    learner_id: str = "demo_learner"   # stable EverOS user_id across sessions

class GenerateResponse(BaseModel):
    plan_id: str
    plan: MissionPlan
    recalled_memory: dict = {}          # label -> recalled snippets used to personalize (memory reveal)

class ConfigResponse(BaseModel):
    plan: MissionPlan
    session_id: str                     # unique per launch, used for reporting
    learner_id: str = "demo_learner"    # lets clients fetch /api/memory/{learner_id}

class NpcChatRequest(BaseModel):
    session_id: str
    mission_id: str
    npc_name: str
    npc_persona: str
    topic: str
    player_message: str
    conversation_history: List[dict] = []  # [{"role": "player"|"npc", "content": "..."}]

class NpcChatResponse(BaseModel):
    npc_reply: str
    is_correct_answer: bool             # true if this reply corresponds to a correct answer to required_question

class ReportEvent(BaseModel):
    session_id: str
    mission_id: str
    # behavior_signal: aggregated engagement observation from the Roblox
    # client (e.g. "idled 90s during puzzle"), never raw input events.
    event_type: Literal["mission_started", "mission_completed", "mission_failed", "answer_submitted", "behavior_signal"]
    payload: dict = {}
