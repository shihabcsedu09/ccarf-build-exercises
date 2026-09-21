"""5.4 Survive a long exploration, and a crash.

Real scenario: after an hour in a large codebase Claude starts describing
"the usual service layer" instead of the OrderRepository it read at minute
ten. Nothing broke; the precise findings are buried under an hour of noise.

Two separate problems, two separate fixes. Get findings out of the
conversation while you work. Get progress onto disk so an interrupted run
resumes instead of restarting.

Run it:
    python ex_5_4_context_resilience.py
"""
import json
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import banner


# ---------------------------------------------------------------- START HERE
def note(scratchpad, finding):
    """Write findings to a file as you go, then read the file later.

    The conversation is where noise accumulates. A file is where facts stay
    retrievable by name instead of by scrolling.
    """
    with scratchpad.open("a") as handle:
        handle.write("- %s\n" % finding)


def delegate(subagent_findings):
    """Send the noisy part somewhere else and keep only what comes back.

    The 400 lines of search output never enter the main context at all.
    """
    return {"searched_lines": 400, "returned": subagent_findings}


def checkpoint(manifest_path, task_id, result):
    """Record progress after every subtask, to durable storage.

    The four things worth writing: what finished, what it produced, where it
    stopped and what failed. Findings are the expensive part.
    """
    manifest = load_manifest(manifest_path)
    manifest["done"].append(task_id)
    manifest["findings"][task_id] = result
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest


def load_manifest(manifest_path):
    if manifest_path.exists():
        return json.loads(manifest_path.read_text())
    return {"done": [], "findings": {}, "failed": {}}


def run_pipeline(tasks, manifest_path, crash_at=None):
    """Resume is a filter over what is already done, not a fresh start."""
    manifest = load_manifest(manifest_path)
    executed = []
    for task in tasks:
        if task in manifest["done"]:
            continue                      # already finished on an earlier run
        if crash_at is not None and task == crash_at:
            raise RuntimeError("process died during %s" % task)
        executed.append(task)
        manifest = checkpoint(manifest_path, task, "result of %s" % task)
    return executed, manifest


def submit_once(ledger, idempotency_key, payload):
    """A crash can land between doing the work and recording it, so the work
    itself has to be safe to repeat."""
    if idempotency_key in ledger:
        return "already submitted, returning the stored result", ledger
    ledger[idempotency_key] = payload
    return "submitted", ledger


if __name__ == "__main__":
    banner("5.4 scratchpads, checkpoints and idempotency", api=False)
    root = pathlib.Path(tempfile.mkdtemp())
    scratchpad = root / "NOTES.md"

    for finding in ["OrderRepository in src/repos/order.py, used by 14 callers",
                    "PricingService applies discounts, not OrderService",
                    "nightly job re-reads the same config; candidate for caching"]:
        note(scratchpad, finding)
    print("scratchpad after exploring:")
    print(scratchpad.read_text().rstrip())
    print("   later you ask Claude to read NOTES.md, instead of scrolling back")
    print("   through an hour of Grep output.")
    print()

    out = delegate(["12 call sites", "2 of them in tests"])
    print("delegated search: %d lines searched, %d findings returned to the main chat"
          % (out["searched_lines"], len(out["returned"])))
    print()

    tasks = ["t1", "t2", "t3", "t4", "t5"]
    manifest_path = root / "state.json"
    try:
        run_pipeline(tasks, manifest_path, crash_at="t4")
    except RuntimeError as exc:
        print("run 1:", exc)
    m = load_manifest(manifest_path)
    print("   manifest on disk: done=%s" % m["done"])
    print()

    executed, m = run_pipeline(tasks, manifest_path)
    print("run 2 after restart: executed %s" % executed)
    print("   skipped %s, because they were already recorded" % m["done"][:3])
    print("   findings from run 1 survived: %d" % len(m["findings"]))
    print()

    ledger = {}
    msg1, ledger = submit_once(ledger, "doc-8891-refund", {"amount": 47.90})
    msg2, ledger = submit_once(ledger, "doc-8891-refund", {"amount": 47.90})
    print("submitting the same work twice after a crash:")
    print("   first  ->", msg1)
    print("   second ->", msg2)
    print("   without the key, the resume pays the refund a second time.")
    shutil.rmtree(root, ignore_errors=True)
