"""5.4 Build a context-resilient codebase explorer.

Degradation is an attention problem, not a token-limit problem. Quality
falls long before the window fills. The fix is to keep findings outside
the conversation.

Run it:  python ex_5_4_context_resilience.py
"""
import json
import os
import tempfile

STATE = os.path.join(tempfile.gettempdir(), "explore_state.json")


# ---------------------------------------------------------------- START HERE
def record(finding):
    """Write to a file, not to the transcript. A file survives compaction."""
    state = load()
    state["findings"].append(finding)
    state["phase"] = finding["phase"]
    with open(STATE, "w") as f:
        json.dump(state, f, indent=2)
    return state


def load():
    if os.path.exists(STATE):
        with open(STATE) as f:
            return json.load(f)
    return {"phase": None, "findings": [], "remaining": []}


def resume_prompt():
    """After a crash, this is the whole briefing. No transcript needed."""
    s = load()
    done = "\n".join(f"  - {f['phase']}: {f['text']}" for f in s["findings"])
    todo = "\n".join(f"  - {t}" for t in s["remaining"])
    return f"Already established:\n{done}\n\nStill to do:\n{todo}"


def delegate(subtask):
    """A subagent reads 40 files and returns 3 lines. The 40 files never
    enter the main window. That is isolation, not just parallelism."""
    files_read = subtask["files"]
    return {"files_read": files_read, "returned_lines": 3,
            "main_context_cost": 3}


def inline(subtask):
    return {"files_read": subtask["files"], "returned_lines": subtask["files"] * 60,
            "main_context_cost": subtask["files"] * 60}


if __name__ == "__main__":
    if os.path.exists(STATE):
        os.remove(STATE)

    s = load()
    s["remaining"] = ["map the payment path", "find the retry policy"]
    with open(STATE, "w") as f:
        json.dump(s, f)

    record({"phase": "entry points", "text": "requests arrive at api/router.py"})
    record({"phase": "auth", "text": "auth is middleware, not per-route"})

    print(resume_prompt())

    task = {"files": 40}
    print("\ninline      :", inline(task))
    print("delegated   :", delegate(task))
    print("\nSame answer. One of them leaves 2400 lines in the window that the")
    print("model must keep attending to for the rest of the session.")
    os.remove(STATE)
