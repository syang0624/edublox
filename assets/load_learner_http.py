"""
EverMind Challenge — Learner Card quickstart loader (EverOS Cloud, raw HTTP).

Same job as load_learner.py, but with NO SDK — just HTTP calls. Use this if
you're not on Python's everos-cloud package (or porting to another language:
the request shape below is identical in JS/Go/curl).

Setup:
    pip install requests
    export EVEROS_API_KEY=<your-api-key>  # from https://everos.evermind.ai/api-keys

Usage:
    python load_learner_http.py maya_chen.json
"""

import json
import os
import sys
import time

import requests

BASE_URL = "https://api.evermind.ai/api/v1"   # EverOS Cloud


def load(path: str) -> None:
    with open(path) as f:
        data = json.load(f)

    api_key = os.environ.get("EVEROS_API_KEY")
    if not api_key:
        sys.exit("Set your key first:  export EVEROS_API_KEY=<your-api-key>   "
                 "(get one at https://everos.evermind.ai/api-keys)")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    learner = data["learner"]
    sessions = data["sessions"]

    print(f"Loading {len(sessions)} sessions for {learner['display_name']} "
          f"(user_id={learner['user_id']})...")

    for s in sessions:
        add_payload = {
            "user_id": s["user_id"],
            "session_id": s["session_id"],
            "messages": s["messages"],
            # async_mode:false = synchronous "accumulated", so the flush below
            # has something to extract. With the default (queued) the flush hits
            # the async queue too early and returns "no_extraction".
            "async_mode": False,
        }
        resp = requests.post(f"{BASE_URL}/memories", headers=headers, json=add_payload)
        resp.raise_for_status()

        # flush = force extraction now (optional in general; we do it so the
        # history is searchable the moment this script finishes).
        flush_payload = {"user_id": s["user_id"], "session_id": s["session_id"]}
        resp = requests.post(f"{BASE_URL}/memories/flush", headers=headers, json=flush_payload)
        resp.raise_for_status()

        print(f"  ✓ {s['session_id']}  ({len(s['messages'])} messages)")
        time.sleep(0.5)

    print("Done. Recall with POST /api/v1/memories/search:")
    print(json.dumps({
        "query": "negative numbers",
        "filters": {"user_id": learner["user_id"]},
        "method": "hybrid",
        "memory_types": ["episodic_memory", "profile"],
        "top_k": 10,
    }, indent=2))


if __name__ == "__main__":
    load(sys.argv[1] if len(sys.argv) > 1 else "maya_chen.json")

# --- Equivalent single call as curl -------------------------------------------
# curl -X POST https://api.evermind.ai/api/v1/memories \
#   -H "Authorization: Bearer $EVEROS_API_KEY" \
#   -H "Content-Type: application/json" \
#   -d '{
#     "user_id": "maya_chen",
#     "session_id": "maya_w1_intro_negatives",
#     "messages": [
#       {"role": "assistant", "timestamp": 1693526400000, "content": "Hi Maya! ..."},
#       {"role": "user",      "timestamp": 1693526418000, "content": "8"}
#     ],
#     "async_mode": false
#   }'
