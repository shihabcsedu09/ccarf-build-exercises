"""5.3 Let failures travel with enough context to recover from.

Real scenario: the search specialist times out on one source category. It
retries three times, then returns "search unavailable". The coordinator now
has two bad options: retry blindly, or fail the whole job.

Handle what is transient where it happens. Pass up what you could not fix,
with what you tried and what you already have.

And a query that ran and found nothing is a success, not a failure.

Run it:
    python ex_5_3_error_propagation.py
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import banner


# ---------------------------------------------------------------- START HERE
def specialist_search(source, world, max_attempts=3):
    """Retry what is transient here, where the query and partial results are.

    Escalating a timeout that a retry would have fixed wastes a coordinator
    round trip. Retrying a permission error wastes three.
    """
    partial = []
    for attempt in range(1, max_attempts + 1):
        outcome = world[source].get("attempt_%d" % attempt, world[source]["default"])

        if outcome == "ok":
            return {"status": "ok", "source": source,
                    "results": world[source]["results"], "attempts": attempt}

        if outcome == "empty":
            # Nothing matched. The query worked, so this is an answer.
            return {"status": "ok", "source": source, "results": [],
                    "note": "query ran; nothing matched", "attempts": attempt}

        if outcome == "forbidden":
            # No number of retries fixes a permission problem.
            return {"status": "failed", "type": "permission", "source": source,
                    "attempts": attempt, "partial_results": partial,
                    "query": world[source]["query"],
                    "alternatives": world[source].get("alternatives", [])}

        partial = world[source].get("partial", [])

    return {"status": "failed", "type": "timeout", "source": source,
            "attempts": max_attempts, "partial_results": partial,
            "query": world[source]["query"],
            "alternatives": world[source].get("alternatives", [])}


def coordinator_decide(reports):
    """What the hub can do, because each report says which kind of failure it was."""
    plan = {}
    for r in reports:
        if r["status"] == "ok":
            plan[r["source"]] = "use %d results" % len(r["results"])
        elif r["type"] == "timeout":
            plan[r["source"]] = ("retry once more, or use %s"
                                 % (", ".join(r["alternatives"]) or "no alternative"))
        else:
            plan[r["source"]] = "cannot be fixed by retrying; note the gap"
    return plan


def synthesise(reports):
    """Graceful degradation: keep what arrived, and say what is missing.

    Failing the whole job throws away work that succeeded. Hiding the gap
    produces a confident report nobody can calibrate.
    """
    covered = [r["source"] for r in reports if r["status"] == "ok" and r["results"]]
    empty = [r["source"] for r in reports if r["status"] == "ok" and not r["results"]]
    missing = [r["source"] for r in reports if r["status"] == "failed"]
    return {
        "findings": sum((r.get("results", []) for r in reports), []),
        "coverage": {
            "well_supported": covered,
            "searched_and_empty": empty,      # evidence of absence, not a gap
            "unavailable": missing,           # a gap, and the reader must know
        },
    }


WORLD = {
    "academic":   {"default": "ok", "results": ["paper A", "paper B"], "query": "q1"},
    "industry":   {"default": "empty", "results": [], "query": "q2"},
    "patents":    {"default": "timeout", "query": "q3", "partial": ["patent X"],
                   "alternatives": ["espacenet", "wipo"]},
    "internal":   {"default": "forbidden", "query": "q4", "alternatives": []},
    "news":       {"default": "timeout", "attempt_2": "ok",
                   "results": ["article C"], "query": "q5"},
}

if __name__ == "__main__":
    banner("5.3 error propagation", api=False)
    reports = [specialist_search(s, WORLD) for s in
               ["academic", "industry", "patents", "internal", "news"]]

    print("what each specialist reported:")
    for r in reports:
        if r["status"] == "ok":
            print("   %-10s ok        %d results after %d attempt(s) %s"
                  % (r["source"], len(r["results"]), r["attempts"], r.get("note", "")))
        else:
            print("   %-10s failed    type=%-11s partial=%d  alternatives=%s"
                  % (r["source"], r["type"], len(r["partial_results"]),
                     r["alternatives"] or "none"))
    print()
    print("news recovered on attempt 2, so the coordinator never heard about it.")
    print()

    print("what the coordinator can now decide:")
    for source, action in coordinator_decide(reports).items():
        print("   %-10s %s" % (source, action))
    print()

    out = synthesise(reports)
    print("the report that goes out:")
    print("   findings:", out["findings"])
    print("   coverage:", json.dumps(out["coverage"]))
    print()
    print("'industry' searched and found nothing, which is a finding. 'patents'")
    print("and 'internal' are gaps. Collapsing those two into one number would")
    print("lose exactly the distinction a reader needs.")
