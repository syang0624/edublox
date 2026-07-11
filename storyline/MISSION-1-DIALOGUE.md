# Mission 1 -- The Briefing (Dialogue Mission)

**Location:** Orbital Station Helios -- Command Deck
**Type:** Dialogue
**Act:** 1 of 3

---

## Scene Description

The cadet spawns on the command deck of Orbital Station Helios. Through the panoramic windows, stars drift slowly past. Holographic displays flicker with data readouts. The deck hums with quiet energy.

Commander Nova stands near the central console, arms behind her back, watching the stars. She turns as the cadet approaches.

## Flow

### 1. Approach Trigger
When the player walks into the `Zone_Trigger` near `NPC_Spawn`, the dialogue UI opens automatically.

### 2. Opening Line
Commander Nova greets the cadet and sets up the context. She frames the study topic as a mission-critical problem aboard the station.

**Example (Solar System topic):**
> "Welcome aboard, cadet! Our star charts glitched and one fact needs re-entering: what keeps all eight planets circling the Sun instead of drifting off into space?"

**Example (Biology topic):**
> "Cadet, our bio-scanner is acting up. Quick check -- what's the name of the process plants use to turn sunlight into food?"

### 3. Conversation Loop
- The player types an answer in the text box and hits Send.
- The message is sent to the backend (`/api/npc-chat`), which calls the LLM.
- The NPC responds in character:
  - **Wrong answer:** Gentle redirect, a small hint if 2+ attempts failed. Never reveals the answer.
  - **Correct answer:** Celebratory in-character line + `[CORRECT]` signal.
- The conversation history is tracked so the NPC remembers what was already said.

### 4. Success
On correct answer:
- The NPC delivers a success line.
- After a 2-second pause, the dialogue UI closes.
- The HUD updates: "Mission 1 Complete -- Proceed to Planet Verdis."
- The `MissionResult` event fires to the server with `success = true`.

### 5. Failure / Leave
- If the player clicks "Leave" before answering correctly, `onComplete(false)` fires.
- The server logs `mission_failed`. The player can retry by approaching the NPC again (stretch goal).

## Roblox Implementation Notes

- NPC Model spawns at `NPC_Spawn` in the orbital station zone.
- Use `DialogueMission.lua` to manage the conversation loop.
- Use `DialogueUI.lua` for the chat window (NPC name, dialogue text, text input, Send/Leave buttons).
- NPC chat is proxied through `Remotes.NpcChat` (RemoteFunction) so the server handles the backend call.
- `max_attempts` defaults to 3 but the NPC keeps going until the player either answers correctly or leaves.

## Design Notes

- The NPC's persona and question are generated from the study PDF -- they are not hardcoded.
- The dialogue should feel like a natural conversation, not a quiz pop-up.
- Commander Nova's tone: confident, warm, brief. Think "supportive coach," not "strict teacher."
