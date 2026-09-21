"""1.7 Resume, fork, or start fresh.

Real scenario: yesterday you spent an hour with Claude working out how the
billing module handles proration, and agreed a plan. Overnight a teammate
merged changes to three of those files.

On the Messages API a session is just the messages list you saved. Resuming
is loading it. Forking is copying it. Starting fresh is writing a summary and
throwing the rest away.

Choose by how much has moved. Three files changed: resume and name them.
Most of the module refactored: start fresh with a summary. Two plans to
compare: fork.

Run it:
    python ex_1_7_sessions.py
"""
import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import banner

YESTERDAY = [
    {"role": "user", "content": "How does billing handle proration?"},
    {"role": "assistant", "content": "Reading billing/proration.py ..."},
    {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1",
                                  "content": "def prorate(days): return days/30  # as of yesterday"}]},
    {"role": "assistant", "content": "Plan: move rounding into prorate() and add a test."},
]


# ---------------------------------------------------------------- START HERE
def save(messages, path):
    """A session is a file. Nothing more mysterious than that."""
    path.write_text(json.dumps(messages, indent=2))
    return path


def resume(path, changed_files):
    """Load yesterday's turns and say what moved, so Claude re-reads only that.

    The old tool results stay in the history. Naming the changed files is what
    stops Claude reasoning from the stale copy.
    """
    messages = json.loads(path.read_text())
    messages.append({"role": "user", "content":
                     "Since yesterday a teammate changed: %s. Re-read those "
                     "before revising the plan. Everything else is as you left it."
                     % ", ".join(changed_files)})
    return messages


def fork(path):
    """Two copies from the same point. Neither one sees the other's work."""
    base = json.loads(path.read_text())
    return list(base), list(base)


def start_fresh(conclusions, changed_note):
    """Keep what you concluded. Throw away every file snapshot."""
    return [{"role": "user", "content":
             "Earlier we concluded:\n%s\n\n%s\nRead the code as it is now "
             "before continuing." % (conclusions, changed_note)}]


def stale_snapshots(messages):
    """How many turns still carry file contents that may have moved on."""
    count = 0
    for m in messages:
        content = m.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    count += 1
    return count


if __name__ == "__main__":
    banner("1.7 resume, fork, or start fresh", api=False)
    tmp = pathlib.Path(tempfile.mkdtemp())
    path = save(YESTERDAY, tmp / "session-billing.json")
    print("saved yesterday's session:", path.name, "(%d turns)" % len(YESTERDAY))
    print()

    r = resume(path, ["session.ts", "token.ts", "middleware.ts"])
    print("RESUME  turns: %d   stale file snapshots still in history: %d"
          % (len(r), stale_snapshots(r)))
    print("        use when a few files moved. The analysis is worth more than")
    print("        the cost of re-reading three files.")
    print()

    a, b = fork(path)
    a.append({"role": "user", "content": "Explore the strangler approach."})
    b.append({"role": "user", "content": "Explore the in-place rewrite."})
    print("FORK    branch A turns: %d   branch B turns: %d   shared history: %d"
          % (len(a), len(b), len(YESTERDAY)))
    print("        use to compare two plans from one analysis. Neither branch")
    print("        sees what the other tried.")
    print()

    f = start_fresh("Rounding belongs inside prorate(), covered by one test.",
                    "About 60% of the module was refactored since, and modules were renamed.")
    print("FRESH   turns: %d   stale file snapshots: %d"
          % (len(f), stale_snapshots(f)))
    print("        use when the code has moved on. The conclusion survives;")
    print("        every file snapshot is gone, so nothing stale can mislead.")
    print()
    print("In Claude Code the same three moves are:")
    print("   claude --resume billing-proration      carry on, then name the changed files")
    print("   claude --continue                      the most recent session here")
    print("   /compact                               context is full, the thread is fine")
