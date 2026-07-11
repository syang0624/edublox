# Mission 3 -- The Discovery (Exploration Mission)

**Location:** The Shardfield -- Asteroid Belt
**Type:** Exploration (Scan & Collect)
**Act:** 3 of 3

---

## Scene Description

The cadet teleports to The Shardfield -- a dense cluster of floating asteroids connected by energy bridges and jump pads. The backdrop is deep space: distant nebulae in violet and indigo, with occasional comets streaking past.

Scattered across the platforms are glowing, scannable objects: crystals, terminals, satellites, and alien specimens. Each is tagged via CollectionService with one of the approved target strings.

## Flow

### 1. Arrival
The player is teleported to `Spawn_asteroid_field`. The HUD updates with:
- The mission prompt explaining what to scan.
- A checklist of 3 target items (unchecked).
- An optional hint.

**Example prompt (Solar System):**
> "Scan 3 objects a solar-system scientist would use or study: the telescope, the star map, and the comet fragment."

**Example prompt (Biology):**
> "Scan 3 specimens that relate to cell structure: the hologram, the sample capsule, and the data crystal."

### 2. Exploration
- The player navigates the asteroid platforms freely.
- Objects are visually distinct and glow with a cyan/indigo outline to indicate they are interactive.
- Some objects on the field are **distractors** -- tagged with valid tags but not part of this mission's target list. Clicking them does nothing (or plays a small "not this one" feedback).

### 3. Scanning
- Player clicks on an object (mouse click / tap).
- The client checks the object's CollectionService tags against the remaining target list.
- **Match:**
  - The object plays a scan animation (pulse effect, particle burst).
  - The HUD checklist updates with a checkmark next to that target.
  - A `CollectTarget` event fires to the server for reporting.
  - The object's glow changes from cyan to green to indicate it's been collected.
- **No match:** Nothing happens (the object isn't part of this mission).

### 4. Completion
When all 3 targets are collected:
- A completion fanfare plays (sound + particle effect).
- The HUD updates: "All specimens collected! Mission complete."
- `MissionResult` fires with `success = true`.
- After a brief pause, the HUD shows the session summary: "Adventure complete! You mastered: [plan title]."

## Available Scannable Objects

These are the 12 approved target tags. The scene should have Parts tagged with each of these scattered across the asteroid field:

| Tag | Visual Description |
|-----|-------------------|
| `data_crystal` | A glowing hexagonal crystal on a rock pedestal |
| `star_map` | A flat holographic star chart floating above a platform |
| `hologram` | A rotating 3D holographic projection |
| `sample_capsule` | A sealed transparent container with a specimen inside |
| `energy_core` | A pulsing orb of contained energy |
| `satellite` | A small orbiting dish with solar panels |
| `rover` | A wheeled exploration vehicle parked on a platform |
| `telescope` | A mounted optical scope pointing at the stars |
| `comet_fragment` | A jagged icy rock with a faint glowing tail |
| `alien_flora` | A bioluminescent plant growing from an asteroid crack |
| `research_terminal` | A standing computer console with a flickering screen |
| `signal_beacon` | A tall antenna with a blinking light on top |

Each mission uses exactly 3 of these. The rest remain in the scene as atmosphere but are not targets for that session.

## Roblox Implementation Notes

- Use `ExplorationMission.lua` to track collected targets and listen for clicks.
- Use `HUD.lua` for the checklist display (`setTargets` / `setTargets` with collected array).
- Click detection uses `UserInputService.InputBegan` + `Players.LocalPlayer:GetMouse().Target`.
- CollectionService tags must be applied in Roblox Studio to the scannable Parts.
- At least 6 tagged objects should be in the scene so there are always some non-target objects present.

## Design Notes

- This mission is about spatial exploration -- the player should need to move around and look.
- Platforms should be spaced so it takes 30-60 seconds of navigation to find all 3 targets.
- The hint text guides without giving exact locations: "Comets are icy leftovers -- look for the glowing shard."
- The feel should be "scavenger hunt in space," not "find the hidden object."
- Objects should be visible from a reasonable distance (glowing outlines help).
