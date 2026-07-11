# Demo Walkthrough -- Solar System Session

A complete scripted playthrough using the demo solar system PDF.

---

## Pre-Session

The player uploads `demo/solar_system.pdf` on the web app. The backend generates a Mission Plan. The player clicks "Launch in Roblox" and joins the place.

If no PDF was uploaded (direct join), the seeded `demo_solar_system` plan loads automatically.

**Plan generated:**
- **Title:** "Voyage Across the Solar System"
- **Topic:** The Solar System
- **Objectives:**
  1. Identify the eight planets in order from the Sun
  2. Explain why inner planets are rocky and outer planets are gas giants
  3. Describe what keeps the planets in orbit around the Sun

---

## Act 1 -- The Briefing

**Location:** Orbital Station Helios

The player spawns on the command deck. Stars drift past the panoramic windows. Commander Nova stands by the central console.

**Commander Nova:**
> "Welcome aboard, cadet! Our star charts glitched and one fact needs re-entering: what keeps all eight planets circling the Sun instead of drifting off into space?"

**Player types:** "magnetism"

**Commander Nova:**
> "Good thinking, but magnetism isn't quite the force at work here. Think about what pulls things toward each other across space..."

**Player types:** "gravity"

**Commander Nova:**
> "That's it -- gravity! The Sun's pull keeps the whole solar system together. Star charts restored, cadet!"

*Dialogue UI closes. HUD: "Mission 1 Complete -- Proceed to Planet Verdis."*

---

## Act 2 -- The Investigation

**Location:** Planet Verdis

The player teleports to the alien planet. The PuzzleTable console activates.

**Prompt:**
> "Restore the research log: arrange the planets in order from closest to the Sun to farthest."

**Items (shuffled):** Saturn, Earth, Mercury, Jupiter, Mars, Venus

**Player arranges:** Mercury, Venus, Earth, Mars, Jupiter, Saturn

**Result:** Correct! The console glows green. "Sequence Restored!"

*HUD: "Mission 2 Complete -- Proceed to The Shardfield."*

---

## Act 3 -- The Discovery

**Location:** The Shardfield

The player teleports to the asteroid belt. Floating platforms stretch into the distance.

**Prompt:**
> "Scan 3 objects a solar-system scientist would use or study: the telescope, the star map, and the comet fragment."

**Hint:**
> "Comets are icy leftovers from when the solar system formed -- look for the glowing shard."

**Checklist:**
- [ ] telescope
- [ ] star_map
- [ ] comet_fragment

The player navigates the platforms:

1. Finds the **telescope** on the second platform. Clicks it. *Scan animation. Checklist updates.*
2. Sees an `energy_core` glowing nearby. Clicks it. *Nothing -- not a target for this mission.*
3. Jumps to a distant platform, finds the **star map** floating above. Clicks it. *Scan animation.*
4. Follows the hint, finds the **comet fragment** on a low asteroid -- a jagged icy rock with a faint glow. Clicks it. *Scan animation.*

**All collected!** Completion fanfare plays.

*HUD: "Adventure complete! You mastered: Voyage Across the Solar System"*

---

## Post-Session

- The backend logs 3 `mission_completed` events.
- EverOS stores the learner's interactions for future personalization.
- The web app can display a session report via `/api/report/{session_id}`.
- Next time this learner uploads a different PDF, EverOS memory will recall their strengths and misconceptions to personalize the new session.
