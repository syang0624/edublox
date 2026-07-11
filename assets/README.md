# Learner Cards — Ready-to-Load Data

**EverMind Challenge · Reinvented Education Hackathon**

This folder is the starter pack for the challenge. Each Learner Card comes with
several weeks of real-feeling learning history, pre-formatted so you can load it
straight into EverOS memory. Once loaded, your build starts as if it had already
tutored the learner for weeks — it *remembers* them. That memory is the whole
point of the theme: **build education AI that gets more valuable the longer it's
used.**

---

## What's in here

| File | What it is |
|------|------------|
| `maya_chen.json`     | Maya, 13 — 7th grade math. Freezes on math, repeats mistakes when anxious. *(Personalized Learning / Assessment)* |
| `daniel_okafor.json` | Daniel, 34 — adult reskiller, English + workplace skills. Studies in short late-night bursts. *(Workforce & Lifelong Learning)* |
| `sofia_reyes.json`   | Sofia, 16 — 10th grade English writing. Improving essayist; growth only shows across the whole portfolio. *(Assessment & Credentialing)* |
| `leo_carter.json`    | Leo, 10 — 5th grade reading, has an IEP. Team needs to track & document progress over time. *(Educator & Institution Tools)* |
| `load_learner.py`      | One-command loader using the `everos-cloud` Python SDK |
| `load_learner_http.py` | Same loader with raw HTTP (no SDK) + an equivalent `curl` example |

Pick **one** learner. Each file's top-level `note_for_builders` field tells you
exactly which memory hooks are embedded and how to show them off in your demo.

---

## Data shape

Each file has a `learner` block (id, bio, and a `note_for_builders` field that
lists the embedded memory hooks) plus a `sessions` list. Every session is a
full, turn-by-turn transcript already shaped for the EverOS add-memory call:

```json
{
  "learner": { "user_id": "maya_chen", "display_name": "Maya Chen", "note_for_builders": "..." },
  "sessions": [
    {
      "user_id": "maya_chen",
      "session_id": "maya_w1_intro_negatives",
      "messages": [
        {"role": "assistant", "timestamp": 1693526400000, "content": "Hi Maya! ..."},
        {"role": "user",      "timestamp": 1693526418000, "content": "8"}
      ]
    }
  ]
}
```

You feed the raw transcripts — **you do not hand-write memory entries**. EverOS's
extraction pipeline distills the conversations into the learner's `profile`
(persistent traits) and `episodic_memory` (what happened) for you. That
auto-extraction is exactly the capability this challenge is about.

> The timestamps are fixed (not "now"), so loading is reproducible and the weekly
> ordering is preserved for a clean demo.

---

## 1. Load a learner into memory

```bash
pip install everos-cloud             # or: pip install requests  (for the HTTP version)
export EVEROS_API_KEY=<your-api-key> # get a key at https://everos.evermind.ai/api-keys

python load_learner.py maya_chen.json
```

The loader `add`s each session synchronously and then `flush`es it, so
extraction finishes *now* rather than in the background — the history is
searchable the moment the script ends, and each week becomes its own clean
episode. (See the `async_mode` note below for why we do it this way and what
your own live app should do instead.)

No SDK? Use `python load_learner_http.py maya_chen.json` — same result over plain
HTTP, with a `curl` example at the bottom of the file.

> **Gotcha if you write your own loader:** call `add(..., async_mode=False)`
> *before* `flush()`. With the default (`async_mode=True`) the messages are
> queued asynchronously, so a `flush()` right after finds nothing accumulated
> and returns `"no_extraction"` — and your memory stays empty. Synchronous add
> returns `"accumulated"`, then `flush()` returns `"extracted"`. (The loaders
> here already do this.)

### `async_mode` — which to use in *your* build

These loaders use `async_mode=False` on purpose: preloading is a one-time
batch, so we trade a bit of speed for certainty that the history is fully
extracted the moment the script ends. **Your live app should NOT copy that** —
use the default `async_mode=True` so `add()` returns instantly and never blocks
the conversation while a learner is typing. Extraction runs in the background
as the dialogue continues.

One thing to remember either way: at the end of a session (or any moment right
before you need to recall), call `flush()`. Extraction is triggered by semantic
boundary detection, and a final chunk of messages with no follow-up won't hit a
boundary on its own — without a flush that last part never gets stored.

| Your situation | Use | Why |
|---|---|---|
| Preloading data (like these loaders) | `async_mode=False` + `flush()` | deterministic, ready the instant loading finishes |
| Live tutoring / chat app | `async_mode=True`, `flush()` at session end | `add()` never blocks the chat; flush secures the last turn |

---

## 2. Recall it in your build

```python
from everos_cloud import EverOS
client = EverOS(api_key="...")

memory = client.v1.memories.search(
    filters={"user_id": "maya_chen"},
    query="negative numbers",
    method="hybrid",
    memory_types=["episodic_memory", "profile"],
    top_k=10,
)
```

Your tutor/assessor/copilot reads that memory before it responds — so in session
5 it can do what it couldn't in session 1.

---

## 3. Make your demo land

None of this is required, but each maps to an EverMind bounty. Pick what fits —
and check your learner's `note_for_builders` for a tailored demo tip.

- **Show more than one session.** Replay an early session, then jump to a later
  one and point out what changed: *"because it remembered X, this time it did Y."*
  → **Best Cross-Session Moment**
- **Throw your own curveball.** Mid-demo, change something — the learner is bored,
  jumped ahead, regressed — and show your AI adapting from what it already knows.
  → **Best Self-Evolving Memory**
- **Open the memory.** Show the actual profile / episodes your build accumulated.
  Makes the compounding visible instead of just claimed. → **Best Memory Reveal**

---

## Questions?

Find the EverMind team in Discord: https://discord.com/invite/gYep5nQRZJ
SDK & docs: https://github.com/EverMind-AI/EverOS · https://docs.evermind.ai
