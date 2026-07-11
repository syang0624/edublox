# Mission 2 -- The Investigation (Puzzle Mission)

**Location:** Planet Verdis -- Research Outpost
**Type:** Puzzle (Ordering)
**Act:** 2 of 3

---

## Scene Description

The cadet teleports to Planet Verdis. The landscape glows with bioluminescent flora -- soft purples, teals, and magentas. Floating rock formations drift overhead. In the center of the outpost sits the **PuzzleTable**: an ancient alien console that displays holographic data fragments.

Ranger Voss stands nearby, scanning the terrain with a handheld device.

## Flow

### 1. Arrival
The player is teleported to `Spawn_alien_planet`. The HUD updates with the mission prompt.

**Example prompt (Solar System):**
> "Restore the research log: arrange the planets in order from closest to the Sun to farthest."

**Example prompt (History):**
> "Restore the research log: arrange these events in chronological order."

### 2. Puzzle Interface
The PuzzleUI opens, showing:
- The prompt at the top.
- A set of 3-6 scrambled items displayed as clickable tiles.
- An "answer slots" area at the bottom where items appear in the order the player clicks them.
- A Submit button.
- A Reset button to clear the current order and start over.

### 3. Interaction
- Player clicks items one at a time. Each clicked item moves to the next answer slot.
- Player can click Reset to try again.
- Player clicks Submit when satisfied with the order.

### 4. Validation
- The order is sent to the server via `Remotes.SubmitPuzzle` (RemoteFunction).
- The server compares against `correct_order` from the Mission Plan. **Validation is server-side only.**
- **Correct:** PuzzleUI shows a success animation (green glow, "Sequence Restored!" text). After 1.5s, UI closes. Mission complete.
- **Incorrect:** PuzzleUI shakes and shows a failure message: "Not quite -- think about the order." Items reset. Player can try again with no attempt limit.

### 5. Completion
- `MissionResult` fires with `success = true`.
- HUD updates: "Mission 2 Complete -- Proceed to The Shardfield."

## Roblox Implementation Notes

- Use `PuzzleMission.lua` to manage the flow.
- Use `PuzzleUI.lua` for the ordering interface.
- Items are presented **shuffled** on the client. The shuffled display order is random each time.
- `correct_order` is an array of indices into the original `items` array. The server has the source of truth.
- No NPC dialogue during this mission (Ranger Voss is set dressing). Keep it focused on the puzzle.

## Design Notes

- The puzzle should feel physical -- like rearranging holographic tiles on an alien console.
- Failure is low-stakes: no lives, no penalty, just a gentle "try again."
- Items should be short enough to read at a glance (5-10 words each max).
- The ordering tests real knowledge from the source material (sequences, rankings, processes, timelines).
