# Madi — Roblox (Luau + Rojo)

## Ownership

Everything under `roblox/`. The Roblox Studio place, Luau scripts, mission modules, UI modules, and scene building.

## Files You Own

```
roblox/
├── src/
│   ├── ServerScriptService/
│   │   ├── MissionRouter.server.lua        # Main server script: load plan, route missions, handle events
│   │   └── BackendClient.lua               # ModuleScript: HTTP calls to backend API
│   ├── StarterPlayerScripts/
│   │   └── ClientBootstrap.client.lua      # LocalScript: receive missions, dispatch to modules
│   ├── ReplicatedStorage/
│   │   ├── Remotes.lua                     # ModuleScript: RemoteEvents/Functions setup
│   │   ├── MissionModules/
│   │   │   ├── DialogueMission.lua         # Dialogue flow + NPC chat via RemoteFunction
│   │   │   ├── PuzzleMission.lua           # Ordering puzzle + server-side validation
│   │   │   └── ExplorationMission.lua      # Click-to-scan tagged objects
│   │   └── UI/
│   │       ├── DialogueUI.lua              # NPC chat window (TextBox + send/leave buttons)
│   │       ├── PuzzleUI.lua                # Item ordering interface + submit button
│   │       └── HUD.lua                     # Top-of-screen status, mission info, exploration checklist
│   └── Workspace/
│       └── (built scene: orbital station, alien planet, asteroid field)
└── default.project.json                    # Rojo config
```

## Task Checklist

### Studio Setup — PRD 6.1
- [ ] Create a new Roblox place and **publish it**
- [ ] Game Settings → Security → **Allow HTTP Requests: ON**
- [ ] Game Settings → Options → **Enable Studio Access to API Services: ON**
- [ ] Get the Place ID from the URL → share with Steven for `NEXT_PUBLIC_ROBLOX_PLACE_ID`
- [ ] Set up Rojo project with `default.project.json`

### Scene Building — PRD 6.1
- [ ] **Orbital Station** zone
  - Metallic command deck with star windows
  - NPC spawn point named `NPC_Spawn`
  - Holographic displays
  - `Zone_Trigger` Part
  - Teleport SpawnLocation named `Spawn_orbital_station`
- [ ] **Alien Planet** zone
  - Colorful low-gravity research zone
  - `PuzzleTable` console
  - Readable paths between landmarks
  - Teleport SpawnLocation named `Spawn_alien_planet`
- [ ] **Asteroid Field** zone
  - Navigable floating platforms
  - 6+ scannable Parts tagged via CollectionService
  - Teleport SpawnLocation named `Spawn_asteroid_field`
- [ ] Tag scannable Parts with approved target strings (via CollectionService):
  `data_crystal`, `star_map`, `hologram`, `sample_capsule`, `energy_core`, `satellite`, `rover`, `telescope`, `comet_fragment`, `alien_flora`, `research_terminal`, `signal_beacon`
- [ ] Art direction: deep navy/black with indigo, violet, and cyan emissive accents. **No** sand, tomb, river-valley, or museum motifs

### Core Scripts
- [ ] **`Remotes.lua`** — PRD 6.2
  - `LoadPlan` (RemoteEvent), `StartMission` (RemoteEvent), `MissionResult` (RemoteEvent)
  - `NpcChat` (RemoteFunction), `SubmitPuzzle` (RemoteFunction), `CollectTarget` (RemoteEvent)
- [ ] **`BackendClient.lua`** — PRD 6.3
  - `getConfig(planId)` → GET `/api/config?plan_id=...`
  - `npcChat(payload)` → POST `/api/npc-chat`
  - `report(event)` → POST `/api/report`
  - All HTTP calls wrapped in `pcall`
  - Hardcode BASE url (get from Nori after backend deploy)
- [ ] **`MissionRouter.server.lua`** — PRD 6.4
  - On `PlayerAdded`: read `launchData` for `plan_id`, fallback to `"demo_solar_system"`
  - Call `BackendClient:getConfig(planId)`, store session per player
  - Fire `LoadPlan` and `StartMission` to client
  - Handle `MissionResult` → advance to next mission or show completion
  - Handle `NpcChat.OnServerInvoke` → proxy to backend
  - Handle `SubmitPuzzle.OnServerInvoke` → server-side order validation
  - Handle `CollectTarget` → report to backend

### Client Scripts
- [ ] **`ClientBootstrap.client.lua`** — PRD 6.5
  - Listen for `LoadPlan` → update HUD (or show completion)
  - Listen for `StartMission` → teleport to location, dispatch to correct mission module
  - Teleport logic: find `Spawn_<location>` in Workspace, PivotTo

### Mission Modules
- [ ] **`DialogueMission.lua`** — PRD 6.6
  - Open DialogueUI with NPC name + opening line
  - On player message: `NpcChat:InvokeServer(mission, text, history)`
  - Track conversation history `{role, content}`
  - On `is_correct_answer == true`: close UI, call `onComplete(true)`
  - On close/leave: call `onComplete(false)`
- [ ] **`PuzzleMission.lua`** — PRD 6.7
  - Open PuzzleUI with prompt + shuffled items
  - On submit: `SubmitPuzzle:InvokeServer(mission_id, order)`
  - Success → close, `onComplete(true)`
  - Failure → show "Try again" message
- [ ] **`ExplorationMission.lua`** — PRD 6.8
  - Track remaining targets from mission data
  - Listen for mouse clicks on Parts
  - Check CollectionService tags against remaining targets
  - On match: fire `CollectTarget` to server, update HUD checklist
  - All targets collected → `onComplete(true)`

### UI Modules
- [ ] **`DialogueUI.lua`** — PRD 6.9
  - ScreenGui with Frame: NPC name label, NPC dialogue label, TextBox input, Send button, Leave button
  - `.open(handlers)`, `.showNpcLine(text)`, `.close()`
- [ ] **`PuzzleUI.lua`** — PRD 6.10
  - Frame with buttons per item, click to append to order, Submit button
  - `.open({prompt, items, onSubmit})`, `.showSuccess()`, `.showFailure(msg)`, `.close()`
- [ ] **`HUD.lua`** — PRD 6.11
  - Top-of-screen status bar
  - `.mount()`, `.setPlanTitle(title)`, `.setMission(mission)`, `.setMissionInstruction(text)`
  - `.setTargets(targets, collectedArray)`, `.setStatus(text)`

### NPC Spawn — PRD 6.12
- [ ] When starting a dialogue mission, spawn NPC Model at correct location
- [ ] Use `Workspace.NPCs.[npc_name]` if it exists, otherwise clone `NPCTemplate` from `ServerStorage`

### Deployment
- [ ] Update `BASE` in `BackendClient.lua` with Nori's deployed backend URL
- [ ] Republish the Roblox place

## Integration Points

| What | Who to coordinate with |
|------|----------------------|
| Place ID | **Steven** — needs it for `NEXT_PUBLIC_ROBLOX_PLACE_ID` |
| `launchData` JSON format (`{"plan_id":"..."}`) | **Steven** — web preview page constructs this deep link |
| Backend BASE URL for `BackendClient.lua` | **Nori** — get the deployed URL |
| `/api/config` response shape | **Nori** — returns `{ plan, session_id }` |
| `/api/npc-chat` request/response | **Nori** — request has session_id, mission_id, npc fields; response has npc_reply + is_correct_answer |
| `/api/report` event format | **Nori** — event_type values: mission_started, mission_completed, mission_failed, answer_submitted |
| Exploration target whitelist | **Nori** — plan_generator only uses the 12 approved tags; scene Parts must be tagged with these same strings |

## Acceptance Criteria

1. Roblox place loads a plan from `launchData` and falls back to `demo_solar_system` if missing
2. Player is teleported to the correct location for each mission
3. **Dialogue**: NPC chat window opens, player can type messages, NPC replies in character, mission ends on correct answer
4. **Puzzle**: items displayed, player orders them, server validates — wrong order shows failure, correct order advances
5. **Exploration**: clicking tagged Parts collects them, HUD checklist updates, all collected → mission complete
6. All 3 missions complete in sequence → HUD shows "Adventure complete!"
7. All `HttpService` calls are wrapped in `pcall` — failures log warnings, never crash the player
8. Puzzle validation is **server-side only** — client never decides success
9. Scene uses Universe theme only: space station, alien planet, asteroid field with navy/indigo/cyan palette
