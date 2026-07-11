"""
EverMind Challenge — Learner Card quickstart loader (EverOS Cloud, Python SDK).

Feeds a learner's full session history into EverOS memory. After this runs,
EverOS has auto-derived the learner's profile + episodic memory, so your build
can start from "session N" — it already remembers the earlier weeks.

Setup:
    pip install everos-cloud
    export EVEROS_API_KEY=<your-api-key>  # from https://everos.evermind.ai/api-keys

Usage:
    python load_learner.py maya_chen.json

Then in your build, recall what was learned:
    client.v1.memories.search(
        filters={"user_id": "maya_chen"},
        query="negative numbers",
        memory_types=["episodic_memory", "profile"],
    )
"""

import json
import os
import sys
import time

from everos_cloud import EverOS  # pip install everos-cloud


def load(path: str) -> None:
    with open(path) as f:
        data = json.load(f)

    api_key = os.environ.get("EVEROS_API_KEY")
    if not api_key:
        sys.exit("Set your key first:  export EVEROS_API_KEY=<your-api-key>   "
                 "(get one at https://everos.evermind.ai/api-keys)")

    client = EverOS(api_key=api_key)
    learner = data["learner"]
    sessions = data["sessions"]

    print(f"Loading {len(sessions)} sessions for {learner['display_name']} "
          f"(user_id={learner['user_id']})...")

    memories = client.v1.memories
    for s in sessions:
        # async_mode=False makes add() SYNCHRONOUS ("accumulated") so the flush
        # right after has something to work on. With the default (queued), the
        # messages are still in the async queue when flush runs, and flush comes
        # back "no_extraction" — nothing gets stored.
        memories.add(
            user_id=s["user_id"],
            session_id=s["session_id"],
            messages=s["messages"],
            async_mode=False,
        )
        # flush then forces extraction NOW (returns "extracted"), so the history
        # is searchable the moment this script finishes and each week becomes its
        # own clean episode.
        memories.flush(user_id=s["user_id"], session_id=s["session_id"])
        print(f"  ✓ {s['session_id']}  ({len(s['messages'])} messages)")
        time.sleep(0.5)  # be gentle on the extraction pipeline

    print("Done. Your learner now has weeks of history in memory.")
    print("Recall it with client.v1.memories.search(filters={'user_id': "
          f"'{learner['user_id']}'}}, query='...').")


if __name__ == "__main__":
    load(sys.argv[1] if len(sys.argv) > 1 else "maya_chen.json")
